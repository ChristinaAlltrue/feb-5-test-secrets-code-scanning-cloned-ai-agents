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
from typing import List, Literal

import requests
from cachetools import TTLCache  # type: ignore
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
CHAT_URL = "https://us-south.ml.cloud.ibm.com"
CHAT_PATH = "/ml/v1/text/chat?version=2023-05-29"

# Configure a cache with a TTL (time-to-live) of 3600 seconds (1 hour)
token_cache = TTLCache(maxsize=1, ttl=3599)


class WatsonXBlockedException(Exception):
    def __init__(self, message: str):
        self.message = message


class WatsonX:
    def __init__(
        self,
        api_key: str,
        endpoint_type: Literal["chat", "ai_service", "text_generation"] = "chat",
        project_id: str | None = None,
        model_id: str | None = None,
        deployment_id: str | None = None,
        api_base: str | None = None,
        custom_headers: list[tuple[str, str]] | None = None,
        system_prompt: str | None = None,
    ):
        if endpoint_type == "chat":
            if not project_id or not model_id:
                raise ValueError(
                    "project_id and model_id are required for chat endpoint"
                )

        else:
            if not deployment_id:
                raise ValueError(
                    "deployment_id is required for ai_service/text_generation endpoint"
                )

        self.api_key = api_key
        self.endpoint_type = endpoint_type
        self.token = get_ibm_token(api_key)
        self.project_id = project_id
        self.deployment_id = deployment_id
        self.model_id = model_id
        self.custom_headers = custom_headers
        self.system_prompt = system_prompt
        self.api_base = api_base if api_base else CHAT_URL

    def get_watson_response(self, messages: List[dict]) -> dict:
        # see if system prompt is in the messages
        if self.system_prompt:
            messages = messages.copy()
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        if self.endpoint_type == "chat":
            return get_watson_chat_response(
                messages,
                api_key=self.api_key,
                model_id=self.model_id,
                project_id=self.project_id,
                api_base=self.api_base,
                custom_headers=self.custom_headers,
            )
        elif self.endpoint_type in ["ai_service", "text_generation"]:
            return get_watson_ai_service_response(
                messages,
                api_key=self.api_key,
                deployment_id=self.deployment_id,
                api_base=self.api_base,
                custom_headers=self.custom_headers,
                endpoint_type=self.endpoint_type,
            )
        else:
            raise ValueError("Invalid endpoint_type")


def fetch_ibm_token(api_key) -> str:
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
    )
    response.raise_for_status()
    token_info = response.json()
    return token_info.get("access_token")


def get_ibm_token(api_key: str) -> str:
    # Return cached token or fetch a new one if cache is expired
    if "access_token" not in token_cache:
        token_cache["access_token"] = fetch_ibm_token(api_key)
    return token_cache["access_token"]


class ForbiddenException(Exception):
    pass


def chat_fetch_and_retry_on_forbidden(
    api_key, model_id, project_id, api_base, messages, headers
):
    """Fetch Watson response and retry with new token on HTTP 403 error."""
    response = requests.post(
        api_base + CHAT_PATH,
        headers=headers,
        json={
            "model_id": model_id,
            "project_id": project_id,
            "max_tokens": 0,
            "random_seed": 0,
            "messages": messages,
        },
    )
    if response.status_code == 401:
        raise ForbiddenException("Access forbidden. Token might be expired.")
    elif response.status_code == 403:
        # if it comes from alltrue, raise it
        response_json = response.json()
        if (
            "errors" in response_json
            and "code" in response_json["errors"][0]
            and response_json["errors"][0]["code"] == "authentication_token_expired"
        ):
            raise ForbiddenException("Access forbidden. Token might be expired.")
        # assume all other 403's are expected from firewall (bad assumption)
        elif "error_from_alltrue_proxy" in response_json:
            raise WatsonXBlockedException(
                message=response_json.get(
                    "message",
                    "Blocked by AllTrue Firewall. Request is blocked due to firewall rules",
                )
            )
        # if it comes from watsonx, raise it

    response.raise_for_status()
    return response.json()


@retry(
    retry=retry_if_exception(lambda e: isinstance(e, ForbiddenException)),
    stop=stop_after_attempt(2),  # Retry twice
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
def get_watson_chat_response(
    messages: List[dict],
    api_key: str,
    model_id: str,
    project_id: str,
    api_base: str,
    custom_headers: list[tuple[str, str]] | None = None,
) -> dict:
    # Static headers irrespective of token
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    if custom_headers:
        headers.update(custom_headers)

    token = get_ibm_token(api_key)
    headers["Authorization"] = f"Bearer {token}"

    try:
        return chat_fetch_and_retry_on_forbidden(
            api_key, model_id, project_id, api_base, messages, headers
        )
    except ForbiddenException:
        # If a 403 error persists, refresh token and retry immediately
        token_cache["access_token"] = fetch_ibm_token(api_key)
        headers["Authorization"] = f'Bearer {token_cache["access_token"]}'
        return chat_fetch_and_retry_on_forbidden(
            api_key, model_id, project_id, api_base, messages, headers
        )


_AI_SERVICE_ENDPOINTS = {
    "ai_service": "/ml/v4/deployments/%s/ai_service?version=2021-05-01",
    "text_generation": "/ml/v1/deployments/%s/text/generation?version=2021-05-01",
}


def ai_service_fetch_and_retry_on_forbidden(
    deployment_id,
    api_base,
    messages,
    headers,
    endpoint_type: Literal["ai_service", "text_generation"],
):
    """Fetch Watson response and retry with new token on HTTP 403 error."""
    response = requests.post(
        api_base + _AI_SERVICE_ENDPOINTS[endpoint_type] % deployment_id,
        headers=headers,
        json={
            "messages": messages,
        },
        verify=False,
    )
    if response.status_code == 401:
        raise ForbiddenException("Access forbidden. Token might be expired.")
    elif response.status_code == 403:
        # if it comes from alltrue, raise it
        response_json = response.json()
        if (
            "errors" in response_json
            and "code" in response_json["errors"][0]
            and response_json["errors"][0]["code"] == "authentication_token_expired"
        ):
            raise ForbiddenException("Access forbidden. Token might be expired.")
        # assume all other 403's are expected from firewall (bad assumption)
        elif "error_from_alltrue_proxy" in response_json:
            raise WatsonXBlockedException(
                message=response_json.get(
                    "message",
                    "Blocked by AllTrue Firewall. Request is blocked due to firewall rules",
                )
            )
        # if it comes from watsonx, raise it

    response.raise_for_status()
    return response.json()


@retry(
    retry=retry_if_exception(lambda e: isinstance(e, ForbiddenException)),
    stop=stop_after_attempt(2),  # Retry twice
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
def get_watson_ai_service_response(
    messages: List[dict],
    api_key: str,
    deployment_id: str,
    api_base: str,
    custom_headers: list[tuple[str, str]] | None = None,
    endpoint_type: Literal["ai_service", "text_generation"] = "ai_service",
) -> dict:
    # Static headers irrespective of token
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    if custom_headers:
        headers.update(custom_headers)

    token = get_ibm_token(api_key)
    headers["Authorization"] = f"Bearer {token}"

    try:
        return ai_service_fetch_and_retry_on_forbidden(
            deployment_id,
            api_base,
            messages,
            headers,
            endpoint_type,
        )
    except ForbiddenException:
        # If a 403 error persists, refresh token and retry immediately
        token_cache["access_token"] = fetch_ibm_token(api_key)
        headers["Authorization"] = f'Bearer {token_cache["access_token"]}'
        return ai_service_fetch_and_retry_on_forbidden(
            deployment_id,
            api_base,
            messages,
            headers,
            endpoint_type,
        )
