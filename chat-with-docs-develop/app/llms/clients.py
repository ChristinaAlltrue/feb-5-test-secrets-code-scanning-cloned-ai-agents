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
import json
import os
import urllib.parse
from typing import Any, List, Optional, Tuple

import boto3
import google.generativeai as genai
import httpx
import logfire
from google.api_core.client_options import ClientOptions
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from langchain_anthropic import ChatAnthropic
from openai import AzureOpenAI, OpenAI

from app.utils.watsonx_requests import CHAT_URL, WatsonX

from .constants import (
    AUTHORIZATION,
    BASE_URL,
    CACHE_CONTROL,
    CUSTOM_AUTHORIZATION,
    DOMAIN_MATCHER,
    ENDPOINT_IDENTIFIER,
    FASTGATE_CONTROL,
    PATH_MATCHER,
    PROXY_TYPE,
    USER_SESSION_INFO,
)

BaseUrlKeyMap = {
    "openai": "openai_api_base",
    "anthropic": "anthropic_api_base",
    "gemini": "gemini_api_base",
    "azure-openai": "azure_openai_api_base",
    "watsonx": "watsonx_api_base",
    "watsonx_assistant": "watsonx_assistant_api_base",
    "watsonx_ai_service_deployment": "watsonx_ai_service_api_base",
    "bedrock": "bedrock_api_base",
}


@logfire.instrument()
def build_proxy_base_url(llm: str, llm_kwargs: dict) -> str:
    key = BaseUrlKeyMap.get(llm)
    if not key:
        raise ValueError(f"Unknown LLM: {llm}")
    base_url = llm_kwargs.get(key, "")
    return urllib.parse.quote(base_url or "", safe=":/")


def _session_headers_template(
    llm: str,
    llm_kwargs: dict,
    optional_params: Optional[dict] = None,
    use_proxy: bool = False,
):
    session_headers: Optional[List[Tuple[str, str]]] = None

    if optional_params:
        session_headers = [(USER_SESSION_INFO, json.dumps(optional_params))]

    endpoint_identifier = llm_kwargs.get("endpoint_identifier")
    if endpoint_identifier:
        session_headers = (session_headers or []) + [
            (ENDPOINT_IDENTIFIER, endpoint_identifier)
        ]

    if llm_kwargs.get("no_cache", False):
        session_headers = (session_headers or []) + [(CACHE_CONTROL, "no-cache")]

    if llm_kwargs.get("no_fastgate", False):
        session_headers = (session_headers or []) + [(FASTGATE_CONTROL, "no-fastgate")]

    proxy_base_url = build_proxy_base_url(llm, llm_kwargs) if use_proxy else None

    return session_headers, proxy_base_url


@logfire.instrument()
def initialize_client(
    llm: str,
    llm_kwargs: dict,
    optional_params: Optional[dict] = None,
    use_proxy: bool = False,
) -> Tuple[Any, Optional[List[Tuple[str, str]]]]:
    session_headers, proxy_base_url = _session_headers_template(
        llm, llm_kwargs, optional_params, use_proxy
    )

    if llm == "openai":
        session_headers = (session_headers or []) + [
            (BASE_URL, "https://api.openai.com/v1"),
            (PROXY_TYPE, "openai"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*/chat/completions.*"]'),
        ]
        client = OpenAI(
            api_key=llm_kwargs.get("openai_api_key"),
            base_url=proxy_base_url,
            default_headers=dict(session_headers),
            max_retries=0,
        )
        logfire.instrument_openai(client)

    elif llm == "anthropic":
        session_headers = (session_headers or []) + [
            (BASE_URL, "https://api.anthropic.com/v1"),
            (PROXY_TYPE, "anthropic"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*/messages.*"]'),
        ]
        client = ChatAnthropic(
            model_name=llm_kwargs.get("anthropic_model_id"),
            api_key=llm_kwargs.get("anthropic_api_key"),
            temperature=0,
            max_tokens_to_sample=1024,
            max_retries=0,
            base_url=proxy_base_url,
            default_headers=dict(session_headers),
        )

    elif llm == "gemini":
        session_headers = (session_headers or []) + [
            (BASE_URL, "https://generativelanguage.googleapis.com"),
            (PROXY_TYPE, "google"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*([Gg]enerate|[Bb]atch[Ee]mbed)[Cc]ontent[s]?.*"]'),
        ]
        if proxy_base_url:
            options = ClientOptions(
                api_endpoint=proxy_base_url.replace("http://", "").replace(
                    "https://", ""
                )
            )
            os.environ["GRPC_DNS_RESOLVER"] = "native"
            os.environ["GRPC_TRACE"] = "call_error"
        else:
            options = ClientOptions()
        genai.configure(
            api_key=llm_kwargs.get("gemini_api_key"),
            transport="rest",
            client_options=options,
            default_metadata=session_headers,
        )
        client = genai.GenerativeModel(llm_kwargs.get("gemini_model_id"))

    elif llm == "azure-openai":
        azure_resource_name = llm_kwargs.get("azure_openai_resource_name")
        base_url = f"https://{azure_resource_name}.openai.azure.com"
        session_headers = (session_headers or []) + [
            (BASE_URL, base_url),
            (PROXY_TYPE, "azure-openai"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*/chat/completions.*"]'),
        ]
        if use_proxy:
            httpx_client = httpx.Client(http2=True, verify=False)
            client = AzureOpenAI(
                api_key=llm_kwargs.get("azure_openai_api_key"),
                base_url=proxy_base_url,
                api_version=llm_kwargs.get("azure_openai_api_version", "2024-06-01"),
                http_client=httpx_client,
                default_headers=dict(session_headers),
                max_retries=0,
            )
        else:
            client = AzureOpenAI(
                api_key=llm_kwargs.get("azure_openai_api_key"),
                azure_endpoint=base_url,
                api_version=llm_kwargs.get("azure_openai_api_version", "2024-06-01"),
                default_headers=dict(session_headers),
            )
        logfire.instrument_openai(client)

    elif llm == "watsonx":
        session_headers = (session_headers or []) + [
            (
                BASE_URL,
                llm_kwargs.get("watsonx_service_url", CHAT_URL),
            ),
            (PROXY_TYPE, "ibmwatsonx"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*/text/chat.*"]'),
        ]
        api_key = llm_kwargs.get("watsonx_api_key")
        if not api_key:
            raise ValueError("watsonx_api_key is required for WatsonX client.")
        client = WatsonX(
            api_key=api_key,
            project_id=llm_kwargs.get("watsonx_project_id"),
            model_id=llm_kwargs.get("watsonx_model_id"),
            api_base=proxy_base_url
            if use_proxy
            else llm_kwargs.get("watsonx_service_url"),
            custom_headers=session_headers,
            system_prompt=llm_kwargs.get("watsonx_system_prompt"),
        )

    elif llm == "watsonx_assistant":
        session_headers = (session_headers or []) + [
            (
                BASE_URL,
                llm_kwargs.get(
                    "watsonx_assistant_service_url",
                    "https://api.us-south.assistant.watson.cloud.ibm.com/",
                ),
            ),
            (PROXY_TYPE, "ibmwatsonx-assistant"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*"]'),
        ]
        authenticator = IAMAuthenticator(
            llm_kwargs.get("watsonx_assistant_api_key"),
            disable_ssl_verification=True,
        )
        client = AssistantV2(version="2021-06-14", authenticator=authenticator)
        # hacking to bypass SSL host check as we disabled SSL verification
        ctx = client.http_adapter.poolmanager.connection_pool_kw.get("ssl_context")
        if ctx:
            ctx.check_hostname = False
        if use_proxy:
            client.set_default_headers(headers=dict(session_headers))
            client.set_service_url(
                proxy_base_url
                + f"instances/{llm_kwargs.get('watsonx_assistant_instance_id')}"
            )
        else:
            client.set_service_url(
                f"{llm_kwargs.get('watsonx_assistant_service_url')}instances/{llm_kwargs.get('watsonx_assistant_instance_id')}"
            )

    elif llm == "watsonx_ai_service_deployment":
        if llm_kwargs.get("watsonx_text_generation_api"):
            endpoint_type = "text_generation"
            extra_headers = [
                (PROXY_TYPE, "any"),
                (
                    "x-alltrue-llm-request-processor",
                    '{"processor_type":"jsonpath","pre-input":"messages[*].content","post-input":"messages[*].content","pre-output":"results[*].generated_text","post-output":"results[*].generated_text"}',
                ),
            ]
        else:
            endpoint_type = "ai_service"
            extra_headers = [
                (PROXY_TYPE, "ibmwatsonx-ai-service"),
            ]

        session_headers = (
            (session_headers or [])
            + [
                (
                    BASE_URL,
                    llm_kwargs.get("watsonx_ai_service_url", CHAT_URL),
                ),
                (DOMAIN_MATCHER, '[".*"]'),
                (PATH_MATCHER, '[".*"]'),
            ]
            + extra_headers
        )
        api_key = llm_kwargs.get("watsonx_ai_service_deployment_api_key")
        if not api_key:
            raise ValueError(
                "watsonx_ai_service_deployment_api_key is required for WatsonX AI Service client."
            )
        client = WatsonX(
            api_key=api_key,
            deployment_id=llm_kwargs.get("watsonx_ai_service_deployment_id"),
            endpoint_type=endpoint_type,  # type: ignore
            api_base=proxy_base_url
            if use_proxy
            else llm_kwargs.get("watsonx_ai_service_url"),
            custom_headers=session_headers,
            system_prompt=llm_kwargs.get("watsonx_ai_service_system_prompt"),
        )

    elif llm == "bedrock":
        region = llm_kwargs.get("bedrock_aws_region")
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=llm_kwargs.get("bedrock_aws_access_key_id"),
            aws_secret_access_key=llm_kwargs.get("bedrock_aws_secret_access_key"),
            aws_session_token=llm_kwargs.get("bedrock_aws_session_token"),
            region_name=region,
            **({"endpoint_url": proxy_base_url} if proxy_base_url else {}),
        )
        if use_proxy:

            def _add_headers(request, **kwargs):
                for name, value in session_headers or []:
                    request.headers[name] = value
                request.headers[PROXY_TYPE] = "bedrock"
                request.headers[DOMAIN_MATCHER] = '[".*"]'
                request.headers[PATH_MATCHER] = '["/model/.*/converse.*"]'
                request.headers[
                    BASE_URL
                ] = f"https://bedrock-runtime.{region}.amazonaws.com"
                request.headers[CUSTOM_AUTHORIZATION] = request.headers[AUTHORIZATION]

            client.meta.events.register(
                "before-send.bedrock-runtime.Converse", _add_headers
            )

    else:
        raise ValueError(f"Unknown LLM: {llm}")

    return client, session_headers


from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider


def initialize_pydantic_ai_model_provider(
    llm: str,
    llm_kwargs: dict,
    optional_params: Optional[dict] = None,
    use_proxy: bool = False,
) -> Model:
    session_headers, proxy_base_url = _session_headers_template(
        llm, llm_kwargs, optional_params, use_proxy
    )

    if llm == "openai":
        from openai import AsyncOpenAI

        if use_proxy:

            session_headers = (session_headers or []) + [
                (BASE_URL, "https://api.openai.com/v1"),
                (PROXY_TYPE, "openai"),
                (DOMAIN_MATCHER, '[".*"]'),
                (PATH_MATCHER, '[".*/chat/completions.*"]'),
            ]

            client = AsyncOpenAI(
                base_url=proxy_base_url,
                api_key=llm_kwargs.get("openai_api_key"),
                default_headers=dict(session_headers) if session_headers else None,
            )
        else:
            client = AsyncOpenAI(
                api_key=llm_kwargs.get("openai_api_key"),
            )

        provider = OpenAIProvider(openai_client=client)
        return OpenAIModel(
            llm_kwargs.get("openai_model_id", "gpt-4o"),
            provider=provider,
        )
    elif llm == "anthropic":
        from anthropic import AsyncAnthropic

        if use_proxy:
            session_headers = (session_headers or []) + [
                (BASE_URL, "https://api.anthropic.com/v1"),
                (PROXY_TYPE, "anthropic"),
                (DOMAIN_MATCHER, '[".*"]'),
                (PATH_MATCHER, '[".*/messages.*"]'),
            ]

            client = AsyncAnthropic(
                api_key=llm_kwargs.get("anthropic_api_key"),
                base_url=proxy_base_url,
                default_headers=dict(session_headers) if session_headers else None,
            )
            provider = AnthropicProvider(anthropic_client=client)
            return AnthropicModel(
                llm_kwargs.get("anthropic_model_id"),
                provider=provider,
            )
        else:
            client = AsyncAnthropic(
                api_key=llm_kwargs.get("anthropic_api_key"),
            )
            provider = AnthropicProvider(anthropic_client=client)
            return AnthropicModel(
                llm_kwargs.get("anthropic_model_id"),
                provider=provider,
            )

    elif llm == "azure-openai":

        from openai import AsyncAzureOpenAI

        azure_resource_name = llm_kwargs.get("azure_openai_resource_name")
        base_url = f"https://{azure_resource_name}.openai.azure.com"

        if use_proxy:
            session_headers = (session_headers or []) + [
                (BASE_URL, base_url),
                (PROXY_TYPE, "azure-openai"),
                (DOMAIN_MATCHER, '[".*"]'),
                (PATH_MATCHER, '[".*/chat/completions.*"]'),
            ]

            client = AsyncAzureOpenAI(
                api_key=llm_kwargs.get("azure_openai_api_key"),
                azure_endpoint=proxy_base_url,
                api_version=llm_kwargs.get("azure_openai_api_version", "2024-06-01"),
                default_headers=dict(session_headers) if session_headers else None,
            )

        else:

            client = AsyncAzureOpenAI(
                api_key=llm_kwargs.get("azure_openai_api_key"),
                azure_endpoint=base_url,
                api_version=llm_kwargs.get("azure_openai_api_version", "2024-06-01"),
            )

        provider = OpenAIProvider(openai_client=client)

        azure_openai_model_id = llm_kwargs.get("azure_openai_model_id")
        if not azure_openai_model_id:
            raise ValueError("azure_openai_model_id is required for Azure OpenAI.")
        return OpenAIModel(
            azure_openai_model_id,
            provider=provider,
        )

    elif llm == "gemini":
        session_headers = (session_headers or []) + [
            (BASE_URL, "https://generativelanguage.googleapis.com"),
            (PROXY_TYPE, "google"),
            (DOMAIN_MATCHER, '[".*"]'),
            (PATH_MATCHER, '[".*([Gg]enerate|[Bb]atch[Ee]mbed)[Cc]ontent[s]?.*"]'),
        ]

        from google.genai import Client
        from google.genai.types import HttpOptions

        if use_proxy:
            client = Client(
                api_key=llm_kwargs.get("gemini_api_key"),
                http_options=HttpOptions(
                    base_url=proxy_base_url, headers=dict(session_headers)
                ),
            )
        else:
            client = Client(
                api_key=llm_kwargs.get("gemini_api_key"),
            )

        provider = GoogleProvider(client=client)
        return GoogleModel(
            llm_kwargs.get("gemini_model_id"),
            provider=provider,
        )

    else:
        raise NotImplementedError("Only OpenAIProvider is implemented so far.")
