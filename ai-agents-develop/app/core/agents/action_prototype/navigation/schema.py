from pydantic import Field

from app.core.agents.base_action_schema.deps_schema import BaseBrowserActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput


class NavigationDeps(BaseBrowserActionDeps):
    instructions: str = Field(..., description="Navigation instructions")
    goal: str = Field(..., description="The goal of navigation")


class NavigationOutput(BaseActionOutput):
    current_url: str = Field(
        ...,
        description="Current URL after navigation",
        json_schema_extra={"example": "https://example.com"},
    )
