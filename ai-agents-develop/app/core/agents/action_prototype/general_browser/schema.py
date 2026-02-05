from typing import List, Literal

from pydantic import Field

from app.core.agents.base_action_schema.deps_schema import BaseBrowserActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput


class GeneralBrowserDeps(BaseBrowserActionDeps):
    instructions: str = Field(..., description="General browser instructions")
    goal: str = Field(..., description="The goal of general browser")
    target_information: str = Field(
        ...,
        description="The information to search for on the pages visited",
    )


class GeneralBrowserOutput(BaseActionOutput):
    current_url: str = Field(
        ...,
        description="Current URL after general browser",
        json_schema_extra={"example": "https://example.com"},
    )
    downloaded_files: List[str] = Field(
        default_factory=list,
        description="List of names of files downloaded during the general browser action",
        json_schema_extra={"example": ["file1.txt", "file2.pdf"]},
    )
    successful: Literal["yes", "no"] = Field(
        ...,
        description="yes or no, whether the general browser was successful",
        json_schema_extra={"example": "yes"},
    )
