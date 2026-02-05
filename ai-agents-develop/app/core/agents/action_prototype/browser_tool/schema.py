from typing import Optional

from pydantic import BaseModel, Field


class BrowserToolParams(BaseModel):
    task: str = Field(..., description="What do you want the Playwright agent to do?")
    homepage_url: str = Field(
        ..., description="The URL of the website to perform the task on"
    )
    skip_login: bool = Field(
        default=False,
        description="Skip login process for sites that don't require authentication",
    )
    username: Optional[str] = Field(
        default=None,
        description="Optional username for login if authentication is required",
    )
    password: Optional[str] = Field(
        default=None,
        description="Optional password for login if authentication is required",
    )
