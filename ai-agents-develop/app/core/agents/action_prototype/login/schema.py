from typing import Optional

from pydantic import Field

from app.core.agents.base_action_schema.deps_schema import BaseBrowserActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput


class LoginDeps(BaseBrowserActionDeps):
    initial_url: str = Field(
        ...,
        description="The starting URL",
        json_schema_extra={"example": "https://example.com"},
    )  # override the initial_url in the base schema
    username: str = Field(
        ...,
        description="Username to log in",
        json_schema_extra={"example": "user@example.com"},
    )
    password: str = Field(..., description="Password for the account")
    instructions: str = Field(..., description="Login flow instructions")
    mfa_secret: Optional[str] = Field("", description="TOTP MFA key")


class LoginOutput(BaseActionOutput):
    pass
