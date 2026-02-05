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

import base64
import json
import logging
from json import JSONDecodeError
from typing import Any, List, Protocol

import botocore.exceptions
import logfire
from anthropic import PermissionDeniedError as AnthropicPermissionDeniedError
from google.api_core.exceptions import Forbidden
from openai import PermissionDeniedError as OpenAIPermissionDeniedError

from app.utils.watsonx_requests import WatsonXBlockedException


def _openai_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    if llm_kwargs.get("openai_use_multi_parts", False):
        ctype = llm_kwargs.get("openai_content_type")
        cfile = llm_kwargs.get("openai_content_file")
        if ctype and cfile:
            b64_data = base64.b64encode(cfile.read()).decode("utf-8")
            if ctype == "image_url":
                content = {
                    "type": ctype,
                    f"{ctype}": {
                        "url": f"data:image/{cfile.name.split('.')[-1].lower()};base64,{b64_data}"
                    },
                }
            elif ctype == "input_audio":
                content = {
                    "type": ctype,
                    f"{ctype}": {"format": cfile.name.split(".")[-1], "data": b64_data},
                }
            else:
                content = {
                    "type": "file",
                    "file": {
                        "filename": cfile.name,
                        "file_data": f"data:application/pdf;base64,{b64_data}",
                    },
                }
            if content:
                m = messages.pop(-1)
                messages.append(
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": m["content"]}, content],
                    }
                )
    response = client.chat.completions.create(
        model=llm_kwargs.get("openai_model_id"), messages=messages
    )
    return response.choices[0].message.content


def _anthropic_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    anthropic_messages = []
    for msg in messages:
        anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
    if not anthropic_messages or anthropic_messages[0]["role"] != "user":
        anthropic_messages.insert(
            0, {"role": "user", "content": "Hello, I have a question."}
        )
    response = client.invoke(anthropic_messages)
    return response.content


def _gemini_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    response = client.generate_content(
        messages[-1]["content"], request_options={"timeout": 30}
    )
    return response.text


def _azure_openai_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    completion = client.chat.completions.create(
        model=llm_kwargs.get("azure_openai_model_id"), messages=messages
    )
    return completion.choices[0].message.content


def _watsonx_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    result = client.get_watson_response(messages=messages)
    if "results" in result:
        return result["results"][0]["generated_text"]
    return result["choices"][0]["message"]["content"]


def _watsonx_assistant_response(
    client: Any,
    messages: List[dict],
    llm_kwargs: dict,
) -> str:
    prompt = messages[-1]["content"]
    assistant_id = llm_kwargs.get("watsonx_assistant_id")
    session_id = llm_kwargs.get("watsonx_assistant_session_id", "")
    session_headers = llm_kwargs.get("watsonx_assistant_session_headers", None)
    response = client.message(
        assistant_id,
        session_id,
        input={"text": prompt},
        verify=False,
        headers=session_headers or [],
    ).get_result()
    output = response["output"]["generic"][0]
    if output.get("text"):
        return output["text"]
    if output.get("response_type") == "search":
        msg = output.get("header", "")
        for result in output.get("primary_results", []) or output.get("results", []):
            highlight = result.get("highlight", {})
            if highlight:
                msg += f"\n\n>{highlight['text'][0]}".replace("<em>", "**").replace(
                    "</em>", "**"
                )
        return msg
    raise ValueError(f"Unknown response type: {output.get('response_type')}")


def _bedrock_response(client: Any, messages: List[dict], llm_kwargs: dict) -> str:
    msgs = [
        {"content": [{"text": m["content"]}], "role": m["role"]} for m in messages[1:]
    ]
    if llm_kwargs.get("bedrock_use_multi_parts", False):
        current = msgs[-1]
        ctype = llm_kwargs.get("bedrock_content_type")
        cfile = llm_kwargs.get("bedrock_content_file")
        if ctype and cfile:
            current["content"].append(
                {
                    ctype: {
                        "format": cfile.name.split(".")[-1],
                        "source": {"bytes": cfile.read()},
                        **(
                            {"name": cfile.name.split("/")[-1].split(".")[0]}
                            if ctype == "document"
                            else {}
                        ),
                    }
                }
            )
    response = client.converse(
        modelId=llm_kwargs.get("bedrock_model_id"), messages=msgs
    )
    return response["output"]["message"]["content"][0]["text"]


class ResponseFunction(Protocol):
    def __call__(self, client: Any, messages: List[dict], llm_kwargs: dict) -> str:
        """Function to get response from LLM."""


_EXECUTORS: dict[str, ResponseFunction] = {
    "openai": _openai_response,
    "anthropic": _anthropic_response,
    "gemini": _gemini_response,
    "azure-openai": _azure_openai_response,
    "watsonx": _watsonx_response,
    "watsonx_ai_service_deployment": _watsonx_response,
    "watsonx_assistant": _watsonx_assistant_response,
    "bedrock": _bedrock_response,
}


@logfire.instrument()
def get_response(
    llm: str,
    client: Any,
    messages: List[dict],
    llm_kwargs: dict,
) -> str:
    try:
        func = _EXECUTORS[llm]
    except KeyError:
        raise ValueError(f"Unknown LLM: {llm}")

    try:
        return func(client, messages, llm_kwargs)
    except (
        OpenAIPermissionDeniedError,
        AnthropicPermissionDeniedError,
        Forbidden,
        WatsonXBlockedException,
    ) as e:
        default_msg = "Permission Denied by AllTrue Firewall. Request is blocked due to firewall rules"
        try:
            try:
                error_json = (
                    e.response.text
                    if hasattr(e, "response")
                    else e.message.lstrip("Error code: 403 - ")
                )
                return json.loads(error_json).get("message")
            except (SyntaxError, ValueError, JSONDecodeError):
                return e.message or default_msg
        except Exception as ex:
            logging.error(f"Error: {str(ex)}\nDetails: {type(ex).__name__}")
            return default_msg
    except botocore.exceptions.ClientError as e:
        return str(e).split("Converse operation:")[-1].lstrip()
    except Exception as e:
        raise RuntimeError(f"Error: {str(e)}\nDetails: {type(e).__name__}") from e
