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

AUTHORIZATION = "Authorization"
CUSTOM_AUTHORIZATION = f"x-alltrue-llm-{AUTHORIZATION.lower()}"
ENDPOINT_IDENTIFIER = "x-alltrue-llm-endpoint-identifier"
BASE_URL = "x-alltrue-llm-base-url"
PROXY_TYPE = "x-alltrue-llm-proxy-type"
DOMAIN_MATCHER = "x-alltrue-llm-domain-matchers"
PATH_MATCHER = "x-alltrue-llm-path-matchers"
USER_SESSION_INFO = "x-alltrue-llm-user-session"
CACHE_CONTROL = "x-alltrue-llm-cache-control"
FASTGATE_CONTROL = "x-alltrue-llm-fastgate-control"
