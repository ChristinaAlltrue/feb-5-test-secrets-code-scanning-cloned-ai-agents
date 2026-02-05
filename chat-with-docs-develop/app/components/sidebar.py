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
import os
import uuid
from typing import Literal, NamedTuple

import logfire
import streamlit as st
from dotenv import load_dotenv
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/assistant_v2.py
from ibm_watson import AssistantV2

from app.utils.watsonx_requests import CHAT_URL
from config import ENV_FILE_PATH

load_dotenv(dotenv_path=ENV_FILE_PATH)


LlmName = Literal[
    "openai",
    "anthropic",
    "gemini",
    "azure-openai",
    "watsonx",
    "watsonx_assistant",
    "watsonx_ai_service_deployment",
    "bedrock",
]


class LlmChoice(NamedTuple):
    llm: LlmName
    display_name: str | None = None


SUPPORTED_LLMS: dict[LlmName, LlmChoice] = {
    "openai": LlmChoice(llm="openai", display_name="OpenAI"),
    "anthropic": LlmChoice(llm="anthropic", display_name="Anthropic"),
    "gemini": LlmChoice(llm="gemini", display_name="Gemini"),
    "azure-openai": LlmChoice(llm="azure-openai", display_name="Azure OpenAI"),
    "watsonx": LlmChoice(llm="watsonx", display_name="WatsonX Foundational Chat Model"),
    "watsonx_assistant": LlmChoice(
        llm="watsonx_assistant", display_name="WatsonX Assistant"
    ),
    "watsonx_ai_service_deployment": LlmChoice(
        llm="watsonx_ai_service_deployment",
        display_name="WatsonX AI Service Deployment",
    ),
    "bedrock": LlmChoice(llm="bedrock", display_name="AWS Bedrock"),
}

optional_params = [
    "Session ID",
    "User ID",
    "User IP",
    "User Role",
    "User Email",
    "User Privileges",
    "Application ID",
    "Application Name",
    "Application Version",
]


def generate_session_id():
    return str(uuid.uuid4())


def request_openai_info():
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="Paste your OpenAI API key here (sk-...)",
        help="You can get your API key from https://platform.openai.com/account/api-keys.",  # noqa: E501
        value=os.environ.get("OPENAI_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("openai_api_key"),
    )

    openai_model_id = st.text_input(
        "OpenAI Model ID",
        key="openai_model_id",
        placeholder="",
        value=os.environ.get("OPENAI_MODEL_ID", "gpt-4o"),
        help="OpenAI Model Name",
    )

    use_multi_parts = st.toggle(
        "Use Multi-Parts Content", key="use_multi_parts", value=False
    )

    openai_content_type = st.selectbox(
        "Content Type",
        options=["image_url", "input_audio", "file"],
        format_func=lambda x: x.replace("_", " ").title(),
        key="openai_content_type",
        disabled=not use_multi_parts,
    )

    openai_content_file = st.file_uploader(
        "Content File",
        key="openai_content_file",
        disabled=not use_multi_parts,
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    openai_api_base = st.text_input(
        "OpenAI API Base URL",
        placeholder="",
        help="Base URL for OpenAI endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("OPENAI_PROXY_BASE", "")
        or st.session_state.get("llm_kwargs", {}).get("openai_api_base", ""),
        disabled=not use_proxy,
    )

    openai_endpoint = st.text_input(
        "Endpoint Identifier",
        key="openai_endpoint",
        value=os.environ.get("OPENAI_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not openai_api_base or openai_api_base.lower() == "none":
        openai_api_base = ""

    # need API key to proceed
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key and base URL")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "openai_api_key": openai_api_key,
        "openai_model_id": openai_model_id,
        "openai_api_base": openai_api_base,
        "openai_use_multi_parts": use_multi_parts,
        "openai_content_type": openai_content_type,
        "openai_content_file": openai_content_file,
        "endpoint_identifier": openai_endpoint,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def _reset_conversation_state():
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]


def request_azure_openai_info():
    openai_api_key = st.text_input(
        "Azure OpenAI API Key",
        type="password",
        placeholder="Paste your Azure OpenAI API key here",
        value=os.environ.get("AZURE_OPENAI_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("openai_api_key"),
    )

    openai_resource_name = st.text_input(
        "Azure OpenAI Resource Name",
        key="azure_openai_resource_name",
        placeholder="",
        value=os.environ.get("AZURE_OPENAI_RESOURCE_NAME", "test-customer"),
        help="Azure OpenAI Resource Name",
    )

    openai_model_id = st.text_input(
        "Azure OpenAI Model Name",
        key="azure_openai_model_id",
        placeholder="",
        value=os.environ.get("AZURE_OPENAI_MODEL_ID", "test"),
        help="Azure OpenAI Model Name",
    )

    openai_api_version = st.text_input(
        "Azure OpenAI API Version",
        key="azure_openai_api_version",
        placeholder="",
        value=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        help="Azure OpenAI API Version",
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    openai_api_base = st.text_input(
        "Azure OpenAI API Base URL",
        placeholder="",
        help="Base URL for Azure OpenAI endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("AZURE_OPENAI_PROXY_BASE", "")
        or st.session_state.get("llm_kwargs", {}).get("openai_api_base", ""),
        disabled=not use_proxy,
    )

    openai_endpoint = st.text_input(
        "Endpoint Identifier",
        key="azure_openai_endpoint",
        value=os.environ.get("AZURE_OPENAI_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
        help="Same as assigning `/endpoint/<ANYTHING>` to API Base URL",
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not openai_api_base or openai_api_base.lower() == "none":
        openai_api_base = ""

    # need API key to proceed
    if not openai_api_key or not openai_resource_name or not openai_model_id:
        st.warning("Please enter your Azure OpenAI API key, Resource Name and Model ID")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "azure_openai_api_key": openai_api_key,
        "azure_openai_resource_name": openai_resource_name,
        "azure_openai_model_id": openai_model_id,
        "azure_openai_api_version": openai_api_version,
        "azure_openai_api_base": openai_api_base,
        "endpoint_identifier": openai_endpoint,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def request_watsonx_info():
    watsonx_api_key = st.text_input(
        "Watsonx API Key",
        type="password",
        placeholder="Paste your WatsonX API key here",
        value=os.environ.get("WATSONX_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("watsonx_api_key"),
    )

    watsonx_service_url = st.text_input(
        "WatsonX Service URL",
        key="watsonx_service_url",
        placeholder="",
        value=CHAT_URL,
        help="WatsonX Service URL",
    )

    watsonx_model_id = st.text_input(
        "WatsonX Model ID",
        key="watsonx_model_id",
        placeholder="",
        value=os.environ.get("WATSONX_MODEL_ID", "ibm/granite-3-2b-instruct"),
        help="ID of Model Foundational Model is Deployed In",
    )

    watsonx_system_prompt = st.text_area(
        "WatsonX System Prompt",
        key="watsonx_system_prompt",
        placeholder="",
        value=None,
        help="System prompt to use for WatsonX model",
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    watsonx_api_base = st.text_input(
        "WatsonX API Base URL",
        placeholder="",
        help="Base URL for WatsonX endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("WATSONX_API_BASE", None)
        or st.session_state.get("llm_kwargs", {}).get("watsonx_api_base", ""),
        disabled=not use_proxy,
    )

    watsonx_project_id = st.text_input(
        "WatsonX Project ID",
        key="watsonx_project_id",
        placeholder="",
        value=os.environ.get("WATSONX_PROJECT_ID", ""),
        disabled=not use_proxy,
        help="ID of Project Foundational Model is Deployed In",
    )

    watsonx_endpoint = st.text_input(
        "Endpoint Identifier",
        key="watsonx_endpoint",
        placeholder="",
        value=os.environ.get("WATSONX_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
        help="Same as assigning `/endpoint/<ANYTHING>` to API Base URL",
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not watsonx_api_base or watsonx_api_base.lower() == "none":
        watsonx_api_base = ""

    # need API key to proceed
    if (
        not watsonx_api_base
        or not watsonx_service_url
        or not watsonx_api_key
        or not watsonx_project_id
    ):
        st.warning(
            "Please enter your Watsonx API key, Service URL, Project ID and and base URL"
        )
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "watsonx_api_key": watsonx_api_key,
        "watsonx_service_url": watsonx_service_url,
        "watsonx_api_base": watsonx_api_base,
        "endpoint_identifier": watsonx_endpoint,
        "watsonx_project_id": watsonx_project_id,
        "watsonx_model_id": watsonx_model_id,
        "watsonx_system_prompt": watsonx_system_prompt,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def request_watsonx_assistant_info():
    watsonx_assistant_api_key = st.text_input(
        "Watsonx Assistant API Key",
        type="password",
        placeholder="Paste your WatsonX Assistant API key here",
        value=os.environ.get("WATSONX_ASSISTANT_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("watsonx_assistant_api_key"),
    )

    watsonx_assistant_service_url = st.text_input(
        "WatsonX Assistant Service URL",
        key="watsonx_assistant_service_url",
        placeholder="",
        value=os.environ.get(
            "WATSONX_ASSISTANT_SERVICE_URL",
            "https://api.us-south.assistant.watson.cloud.ibm.com/",
        ),
        help="Service URL for WatsonX Assistant",
    )
    watsonx_assistant_instance_id = st.text_input(
        "WatsonX Assistant Instance ID",
        key="watsonx_assistant_instance_id",
        placeholder="",
        value=os.environ.get("WATSONX_ASSISTANT_INSTANCE_ID"),
        help="ID of WatsonX Assistant Instance",
    )

    watsonx_assistant_id = st.text_input(
        "WatsonX Assistant ID",
        key="watsonx_assistant_id",
        placeholder="",
        value=os.environ.get(
            "WATSONX_ASSISTANT_ID", "94c57884-759b-4932-8720-b5928f9493c7"
        ),
        help="ID of WatsonX Assistant",
    )

    # need API key to proceed
    if (
        not watsonx_assistant_api_key
        or not watsonx_assistant_id
        or not watsonx_assistant_service_url
    ):
        st.warning(
            "Please enter your Watsonx Assistant API key, Assistant ID, Service URL and and base URL",
        )
        logfire.warn(
            "Missing Watsonx Assistant API key, Assistant ID, Service URL and and base URL",
            watsonx_assistant_api_key=watsonx_assistant_api_key,
            watsonx_assistant_id=watsonx_assistant_id,
            watsonx_assistant_service_url=watsonx_assistant_service_url,
        )
        st.stop()

    # create a watsonx session id if not already created
    if not st.session_state.get("watsonx_assistant_session_id"):
        st.session_state[
            "watsonx_assistant_session_id"
        ] = _create_watsonx_assistant_session_id(
            watsonx_assistant_api_key,
            watsonx_assistant_service_url,
            watsonx_assistant_instance_id,
            watsonx_assistant_id,
        )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    watsonx_assistant_api_base = st.text_input(
        "WatsonX API Base URL",
        placeholder="",
        help="Base URL for WatsonX Assistant endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("WATSONX_ASSISTANT_API_BASE", None)
        or st.session_state.get("llm_kwargs", {}).get("watsonx_assistant_api_base", ""),
        disabled=not use_proxy,
    )

    watsonx_assistant_endpoint = st.text_input(
        "Endpoint Identifier",
        key="watsonx_assistant_endpoint",
        placeholder="",
        value=os.environ.get("WATSONX_ASSISTANT_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
        help="Same as assigning `/endpoint/<ANYTHING>` to API Base URL",
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not watsonx_assistant_api_base or watsonx_assistant_api_base.lower() == "none":
        watsonx_assistant_api_base = ""

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "watsonx_assistant_api_key": watsonx_assistant_api_key,
        "watsonx_assistant_api_base": watsonx_assistant_api_base,
        "endpoint_identifier": watsonx_assistant_endpoint,
        "watsonx_assistant_id": watsonx_assistant_id,
        "watsonx_assistant_service_url": watsonx_assistant_service_url,
        "watsonx_assistant_instance_id": watsonx_assistant_instance_id,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def request_watsonx_ai_service_deployment_info():
    watsonx_api_key = st.text_input(
        "Watsonx API Key",
        type="password",
        placeholder="Paste your WatsonX API key here",
        value=os.environ.get(
            "WATSONX_AI_SERVICE_DEPLOYMENT_API_KEY",
            os.environ.get("WATSONX_API_KEY", None),
        )
        or st.session_state.get("llm_kwargs", {}).get(
            "watsonx_ai_service_deployment_api_key"
        ),
    )

    watsonx_ai_service_url = st.text_input(
        "WatsonX AI Service URL",
        key="watsonx_ai_service_url",
        placeholder="",
        value=CHAT_URL,
        help="WatsonX AI Service URL",
    )

    watsonx_ai_service_deployment_id = st.text_input(
        "WatsonX AI Service Deployment ID",
        key="watsonx_ai_service_deployment_id",
        placeholder="",
        value=os.environ.get("WATSONX_AI_SERVICE_DEPLOYMENT_ID", ""),
        help="ID of AI Service Deployment",
    )

    watsonx_text_generation_api = st.checkbox(
        "Use Text Generation API",
        key="text_generation_api",
        help="Use `/text/generation` API",
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    watsonx_ai_service_api_base = st.text_input(
        "WatsonX API Base URL",
        placeholder="",
        help="Base URL for WatsonX endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("WATSONX_AI_SERVICE_API_BASE", None)
        or st.session_state.get("llm_kwargs", {}).get("watsonx_ai_servce_api_base", ""),
        disabled=not use_proxy,
    )

    watsonx_ai_service_endpoint = st.text_input(
        "Endpoint Identifier",
        key="watsonx_ai_service_endpoint",
        placeholder="",
        value=os.environ.get("WATSONX_AI_SERVICE_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
        help="Same as assigning `/endpoint/<ANYTHING>` to API Base URL",
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not watsonx_ai_service_api_base or watsonx_ai_service_endpoint.lower() == "none":
        watsonx_ai_service_api_base = ""

    # need API key to proceed
    if (
        not watsonx_api_key
        or not watsonx_ai_service_url
        or not watsonx_ai_service_deployment_id
    ):
        st.warning("Please enter your Watsonx API key, Service URL and deployment ID")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "watsonx_ai_service_deployment_api_key": watsonx_api_key,
        "watsonx_ai_service_url": watsonx_ai_service_url,
        "watsonx_text_generation_api": watsonx_text_generation_api,
        "watsonx_ai_service_api_base": watsonx_ai_service_api_base,
        "endpoint_identifier": watsonx_ai_service_endpoint,
        "watsonx_ai_service_deployment_id": watsonx_ai_service_deployment_id,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def _create_watsonx_assistant_session_id(
    watsonx_assistant_api_key: str,
    watsonx_assistant_service_url: str,
    watsonx_instance_id: str,
    watsonx_assistant_id: str,
) -> str:
    authenticator = IAMAuthenticator(
        apikey=watsonx_assistant_api_key,  # disable_ssl_verification=True
    )
    assistant = AssistantV2(version="2020-04-01", authenticator=authenticator)
    assistant.set_service_url(
        f"{watsonx_assistant_service_url}instances/{watsonx_instance_id}"
    )
    response = assistant.create_session(watsonx_assistant_id).get_result()
    return response["session_id"]


def request_anthropic_info():
    anthropic_api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="Paste your Anthropic API key here (sk-...)",
        help="You can get your API key from https://claude.ai",  # noqa: E501
        value=os.environ.get("ANTHROPIC_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("anthropic_api_key"),
    )

    anthropic_model_id = st.text_input(
        "Anthropic Model Name",
        key="anthropic_model_id",
        placeholder="",
        value=os.environ.get("ANTHROPIC_MODEL_ID", "claude-sonnet-4-20250514"),
        help="Anthropic Model Name",
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    anthropic_api_base = st.text_input(
        "Anthropic API Base URL",
        placeholder="",
        help="Base URL for Anthropic endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("ANTHROPIC_PROXY_BASE", "")
        or st.session_state.get("llm_kwargs", {}).get("anthropic_api_base", ""),
        disabled=not use_proxy,
    )

    anthropic_endpoint = st.text_input(
        "Endpoint Identifier",
        key="anthropic_endpoint",
        value=os.environ.get("ANTHROPIC_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not anthropic_api_base or anthropic_api_base.lower() == "none":
        anthropic_api_base = ""

    # need API key to proceed
    if not anthropic_api_key:
        st.warning("Please enter your Anthropic API key and base URL")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "anthropic_api_key": anthropic_api_key,
        "anthropic_model_id": anthropic_model_id,
        "anthropic_api_base": anthropic_api_base,
        "endpoint_identifier": anthropic_endpoint,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def request_gemini_info():
    gemini_api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="Paste your Google Gemini API key here (sk-...)",
        help="You can get your API key from https://google-url.",  # noqa: E501
        value=os.environ.get("GEMINI_API_KEY", None)
        or st.session_state.get("llm_kwargs", {}).get("openai_api_key"),
    )

    gemini_model_id = st.text_input(
        "Gemini Model Name",
        key="gemini_model_id",
        placeholder="",
        value=os.environ.get("GEMINI_MODEL_ID", "gemini-2.5-flash"),
        help="Gemini Generative Model",
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    gemini_api_base = st.text_input(
        "Gemini API Base URL",
        key="gemini_api_base",
        placeholder="",
        help="Base URL for Google Gemini endpoint. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("GEMINI_PROXY_BASE", "")
        or st.session_state.get("llm_kwargs", {}).get("gemini_api_base", ""),
        disabled=not use_proxy,
    )

    gemini_endpoint = st.text_input(
        "Endpoint Identifier",
        key="gemini_endpoint",
        value=os.environ.get("GEMINI_ENDPOINT_IDENTIFIER", ""),
        disabled=not use_proxy,
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not gemini_api_base or gemini_api_base.lower() == "none":
        gemini_api_base = ""

    # need API key to proceed
    if not gemini_api_key:
        st.warning("Please enter your Google Gemini API key and base URL")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "gemini_api_key": gemini_api_key,
        "gemini_model_id": gemini_model_id,
        "gemini_api_base": gemini_api_base,
        "endpoint_identifier": gemini_endpoint,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def request_bedrock_info():
    aws_access_key_id = st.text_input(
        "AWS Access Key ID",
        type="password",
        key="bedrock_aws_access_key_id",
        placeholder="Paste your AWS ACCESS KEY ID here",
        value=os.environ.get("AWS_ACCESS_KEY_ID", None)
        or st.session_state.get("llm_kwargs", {}).get("bedrock_aws_access_key_id"),
    )

    aws_secret_access_key = st.text_input(
        "AWS Secret Access Key",
        type="password",
        key="bedrock_aws_secret_access_key",
        placeholder="Paste your AWS SECRET ACCESS KEY here",
        value=os.environ.get("AWS_SECRET_ACCESS_KEY", None),
    )

    aws_session_token = st.text_input(
        "AWS Session Token",
        type="password",
        key="bedrock_aws_session_token",
        placeholder="Paste your AWS SESSION TOKEN here",
        value=os.environ.get("AWS_SESSION_TOKEN", None),
    )

    aws_region = st.text_input(
        "AWS Region",
        key="bedrock_aws_region",
        placeholder="Paste your AWS Region here",
        value=os.environ.get("AWS_REGION", "us-west-2"),
    )

    bedrock_model_id = st.text_input(
        "Bedrock Model Name",
        key="bedrock_model_id",
        placeholder="",
        value=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
    )

    use_multi_parts = st.toggle(
        "Use Multi-Parts Content", key="use_multi_parts", value=False
    )

    bedrock_content_type = st.selectbox(
        "Content Type",
        options=["image", "video", "document"],
        format_func=lambda x: x.replace("_", " ").title(),
        key="bedrock_content_type",
        disabled=not use_multi_parts,
    )

    bedrock_content_file = st.file_uploader(
        "Content File",
        key="bedrock_content_file",
        disabled=not use_multi_parts,
    )

    # toggle for if using a proxy
    use_proxy = st.toggle("Use Proxy", key="use_proxy")

    # ask for base url. Only enabled if use_proxy is checked
    bedrock_api_base = st.text_input(
        "Bedrock API Base URL",
        key="bedrock_api_base",
        placeholder="",
        help="Base URL for Bedrock. Set to proxy if applicable.",  # noqa: E501
        value=os.environ.get("BEDROCK_PROXY_BASE", "")
        or st.session_state.get("llm_kwargs", {}).get("bedrock_api_base", ""),
        disabled=not use_proxy,
    )

    bedrock_endpoint_identifier = st.text_input(
        "Endpoint Identifier",
        key="bedrock_endpoint_identifier",
        placeholder="",
        disabled=not use_proxy,
    )

    no_cache = st.checkbox(
        "Disable Cache",
        key="no_cache",
        help="Whether to disable system cache",
        disabled=not use_proxy,
    )

    no_fastgate = st.checkbox(
        "Disable Fastgate",
        key="no_fastgate",
        help="Whether to disable Fastgate optimization",
        disabled=not use_proxy,
    )

    if not bedrock_api_base or bedrock_api_base.lower() == "none":
        bedrock_api_base = ""

    # need API key to proceed
    if not aws_access_key_id or not aws_secret_access_key or not aws_region:
        st.warning("AWS Access Keys and Region are required")
        st.stop()

    # set the llm kwargs in the session state
    st.session_state["llm_kwargs"] = {
        "bedrock_api_base": bedrock_api_base,
        "bedrock_api_key": aws_access_key_id,  # placeholder
        "bedrock_aws_access_key_id": aws_access_key_id,
        "bedrock_aws_secret_access_key": aws_secret_access_key,
        "bedrock_aws_session_token": aws_session_token,
        "bedrock_aws_region": aws_region,
        "bedrock_model_id": bedrock_model_id,
        "endpoint_identifier": bedrock_endpoint_identifier,
        "bedrock_use_multi_parts": use_multi_parts,
        "bedrock_content_type": bedrock_content_type,
        "bedrock_content_file": bedrock_content_file,
        "no_cache": no_cache,
        "no_fastgate": no_fastgate,
    }


def select_llm(providers: set[LlmName] | None = None):
    custom_css = """
    <style>
    div[data-baseweb="select"] > div {
        cursor: pointer;
    }
    </style>
    """
    options = list(SUPPORTED_LLMS.keys())
    if providers:
        options = [opt for opt in options if opt in providers]
    st.markdown(custom_css, unsafe_allow_html=True)
    llm = st.selectbox(
        "LLM Model",
        options=options,
        format_func=lambda x: SUPPORTED_LLMS[x].display_name
        or x.replace("-", " ").title(),
        key="llm",
    )
    return llm


def add_optional_params():
    st.subheader("Optional Parameters")
    params = {}
    for param in optional_params:
        key = "user-session-" + param.replace(" ", "-").lower().removeprefix("session-")
        if key == "user-session-id" and key not in st.session_state:
            st.session_state[key] = generate_session_id()

        value = st.text_input(param, value=st.session_state.get(key, ""), key=key)
        if value:
            params[key] = value
    return params


def sidebar(
    providers: set[LlmName] | None = None,
    show_use_optional_params: bool = True,
    show_reset_conversation: bool = True,
):
    with st.sidebar:
        st.markdown(
            "## How to use\n"
            "1. Select the LLM you want to use, and insert necessary information that follows.\n"  # noqa: E501
            "2. Toggle proxy on/off, and configure proxy URL if on\n"
        )

        # first require the llm
        llm = select_llm(providers=providers)
        if llm == "openai":
            request_openai_info()
        elif llm == "anthropic":
            request_anthropic_info()
        elif llm == "gemini":
            request_gemini_info()
        elif llm == "azure-openai":
            request_azure_openai_info()
        elif llm == "watsonx":
            request_watsonx_info()
        elif llm == "watsonx_assistant":
            request_watsonx_assistant_info()
        elif llm == "watsonx_ai_service_deployment":
            request_watsonx_ai_service_deployment_info()
        elif llm == "bedrock":
            request_bedrock_info()

        if show_use_optional_params:
            # optional parameters
            use_optional_params = st.toggle("Add optional parameters", value=True)

            if use_optional_params:
                optional_params_dict = add_optional_params()
                st.session_state["optional_params"] = optional_params_dict
            else:
                st.session_state["optional_params"] = {}

        if show_reset_conversation:
            st.button(
                "Reset Conversation",
                on_click=_reset_conversation_state,
            )

        return llm
