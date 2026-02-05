from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.core.agents.compliance_agent.models import EvidenceItem


class AuditAnalysisBrowserAgentDeps(BaseModel):
    # target_business_unit: List[str] = Field(
    #     ...,
    #     description="List of business units that the agent should check",
    # )
    target_url: str = Field(
        ...,
        description="The target URL to navigate to after authentication",
    )
    task: str = Field(
        ...,
        description="The task instructions for the browser agent to execute",
    )
    username: str = Field(
        ...,
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        description="Password",
    )
    storage_state_path: str | None = Field(
        None,
        description="Path to store Playwright authentication state. If not provided, will be auto-generated from target_url and username",
    )


class AuditAnalysisBrowserAgentOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    successful: bool = Field(
        ...,
        description="Whether the Browser Agent executed successfully",
    )
    feedback: str = Field(
        ...,
        description="The feedback from the browser agent execution",
    )
    execution_flow: str = Field(
        ...,
        description="The execution flow of the browser agent",
    )
    files: List[str] = Field(
        ...,
        description="The file paths that were downloaded",
    )
    business_units: List[str] = Field(
        ...,
        description="The business units that were processed",
    )
    downloaded_count: int = Field(
        ...,
        description="The number of files successfully downloaded",
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence items from the browser agent execution",
    )
