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
from app.utils.secret_router.secret_router_factory import (
    SecretKey,
    SecretScope,
    get_secret_router,
)


class GeminiSecret:
    @classmethod
    def retrieve_key(cls, context=None):
        if context is None:
            context = {"source": "default context"}
        secret_router = get_secret_router()
        token = secret_router.get_secret(
            SecretKey("agents-gemini-api-key"),
            scope=SecretScope.internal(),
        )
        return token


GEMINI_API_KEY = GeminiSecret.retrieve_key()
