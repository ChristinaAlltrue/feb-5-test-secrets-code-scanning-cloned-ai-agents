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
import logfire
import streamlit as st

from app.components.sidebar import sidebar
from app.llms import get_response, initialize_client

dotenv.load_dotenv()

logfire.configure(
    send_to_logfire="if-token-present",
    scrubbing=False,
    service_name="streamlit-basic-chatbot",
)
logfire.instrument_httpx(capture_all=True)
logfire.instrument_requests()
logfire.instrument_aiohttp_client()

st.set_page_config(page_title="Basic Chatbot", page_icon="🤖", layout="wide")
st.header("🤖Basic Chatbot")

# request from user to select llm, and enter necessary information for llm. Will stop if missing information
sidebar()

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    llm = st.session_state["llm"]
    llm_kwargs = st.session_state.get("llm_kwargs", {})
    api_key = llm_kwargs.get(f"{llm.replace('-', '_')}_api_key")
    if not api_key:
        st.info(f"Please add your {llm.capitalize()} API key to continue.")
        st.stop()

    client, session_headers = initialize_client(
        llm,
        llm_kwargs,
        st.session_state.get("optional_params"),
        st.session_state.get("use_proxy", False),
    )
    st.session_state["session_headers"] = session_headers

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        llm_kwargs_copy = llm_kwargs.copy()
        llm_kwargs_copy["watsonx_assistant_session_id"] = st.session_state.get(
            "watsonx_assistant_session_id"
        )
        llm_kwargs_copy["session_headers"] = session_headers

        msg = get_response(
            llm,
            client,
            st.session_state.messages,
            llm_kwargs_copy,
        )
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").markdown(msg)
