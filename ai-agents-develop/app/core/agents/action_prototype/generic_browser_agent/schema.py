from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.core.agents.compliance_agent.models import EvidenceItem
from app.core.graph.deps.action_deps import ActionDeps


class GenericBrowserAgentDeps(ActionDeps):
    # task: str = Field(
    #     ...,
    #     description="The specific task instructions for the browser agent to execute",
    #     example="Navigate to example.com and extract all product information from the page",
    # )
    max_steps: int = Field(
        default=20,
        description="Maximum number of steps the agent can take",
    )
    model_name: str = Field(
        default="gpt-4.1",
        description="The LLM model to use for browser automation",
    )
    use_vision: bool = Field(
        default=False,
        description="Whether to enable vision capabilities for screenshot analysis",
    )
    excluded_actions: Optional[List[str]] = Field(
        default=None,
        description="List of browser actions to exclude from the agent",
    )

    storage_state_path: str = Field(
        description="Path to the Playwright storage state file for session persistence",
    )

    username: str = Field(
        description="Username for login if required by the target website",
    )  # breaking change

    password: str = Field(
        description="Password for login if required by the target website",
    )  # breaking change


class File(BaseModel):
    name: str = Field(
        description="Name of the file",
    )
    full_path: str = Field(
        default=None,
        description="Full path of the file",
    )


class GenericBrowserAgentOutput(BaseModel):
    feedback: str
    successful: Literal["yes", "no"] = Field(
        description="Whether the task is finished successfully",
    )
    execution_flow: str = Field(
        description="The execution flow and steps taken by the browser agent",
    )
    files: List[File] = Field(
        default=None,
        description="List of files downloaded or created during execution",
    )


class GenericBrowserAgentActionOutput(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description="Whether the browser agent finished the task successfully",
    )
    feedback: str = Field(
        description="The feedback from the browser agent about task execution",
    )
    execution_flow: str = Field(
        description="The execution flow and steps taken by the browser agent",
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any data extracted or collected during task execution",
    )
    files: Optional[List[str]] = Field(
        default=None,
        description="List of files downloaded or created during execution with full paths",
    )
    evidence: Optional[List[EvidenceItem]] = Field(
        default=None,
        description="Evidence items containing screenshots, files, or other artifacts from task execution",
    )
