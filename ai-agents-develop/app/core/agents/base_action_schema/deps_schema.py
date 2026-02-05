from typing import Dict, Optional

from pydantic import BaseModel, Field, SecretStr


class BaseActionDeps(BaseModel):
    pass


class BaseBrowserActionDeps(BaseActionDeps):
    initial_url: Optional[str] = Field(
        None,
        description="The starting URL, if not provided, the page from the previous action will be used",
        json_schema_extra={"example": "https://example.com"},
    )
    max_steps: Optional[int] = Field(
        6,
        description="The maximum number of steps to take, if not provided, the default value will be used",
        json_schema_extra={"example": 6},
    )


class BaseCredentialActionDeps(BaseActionDeps):
    credentials: Dict[str, SecretStr] = Field(
        ...,
        description="The credentials to use for the action",
    )
