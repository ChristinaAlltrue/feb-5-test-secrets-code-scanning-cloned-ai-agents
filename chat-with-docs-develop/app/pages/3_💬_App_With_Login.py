#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.
import dotenv
import streamlit as st
from openai import OpenAI

from app.components.sidebar import sidebar

dotenv.load_dotenv()


# request from user to select llm, and enter necessary information for llm. Will stop if missing information
sidebar()


# Authentication
def authenticate(username, password):
    return password == "password" and username == "user"


# Chat functionality
def chat_response(prompt):
    # Simulated processing delay
    import time

    time.sleep(2)  # Simulate response delay
    return f"Response to: {prompt}"


def sign_in() -> bool:  # type: ignore
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Sign In")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")

        if st.button("Submit"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.success("Sign in successful!")
                return True
            else:
                st.error("Invalid username or password.")
                return False
    else:
        return True


def chat_interface():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "How can I help you?"}
        ]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not st.session_state.get("llm_kwargs", {}).get(
            f"{st.session_state['llm'].replace('-', '_')}_api_key", None
        ):
            st.info(
                f"Please add your {st.session_state['llm'].capitalize()} API key to continue."
            )
            st.stop()

        client = initialize_client()
        execute_prompt(prompt, client)


def initialize_client():
    # first extract the llm from the session state
    client = OpenAI(
        api_key=st.session_state.get("llm_kwargs", {}).get("openai_api_key")
    )
    return client


def execute_prompt(prompt: str, client):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    message_with_context = [
        {
            "role": "system",
            "content": "You are a helpful assistant. You give helpful and expert advice.",
        },
        *st.session_state.messages,
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=message_with_context
        )
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

    except Exception as e:
        msg = f"Error: {str(e)}\nDetails: {type(e).__name__}"
        st.error(msg)
        st.stop()


@st.dialog("Are you sure you want to reset the chat?")
def reset_chat():
    st.markdown(
        """
        ## Are you sure you want to reset?

        This will clear the chat history. You cannot undo this action. It's irreversible. For real. Like permanently.
        """
    )
    if st.button("Yes, reset the chat."):
        st.session_state.chat_history[st.session_state.selected_dir] = []
        st.session_state.chat_lock = False
        st.session_state.messages = []
        st.rerun()


# Streamlit App
def main():
    if not sign_in():
        st.stop()

    if st.button("Reset Chat"):
        reset_chat()

    if "chat_lock" not in st.session_state:
        st.session_state.chat_lock = False
    if "selected_dir" not in st.session_state:
        st.session_state.selected_dir = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    # Login screen
    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")

        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")
                st.stop()

    # Directory listing
    st.title("Directories")
    directories = [f"Directory {i}" for i in range(1, 6)]  # Example directories

    if st.session_state.selected_dir is None:
        for directory in directories:
            if st.button(directory):
                st.session_state.selected_dir = directory
                if directory not in st.session_state.chat_history:
                    st.session_state.chat_history[directory] = []
                st.rerun()
    else:
        chat_interface()


if __name__ == "__main__":
    main()
