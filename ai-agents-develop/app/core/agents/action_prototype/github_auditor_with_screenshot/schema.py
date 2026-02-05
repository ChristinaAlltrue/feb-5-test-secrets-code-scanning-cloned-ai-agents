from typing import List, Literal

from pydantic import BaseModel, Field

from app.core.agents.action_prototype.github_auditor_with_screenshot.tools.github_evidence_screenshot import (
    ScreenshotEvidence,
)
from app.core.agents.base_action_schema.output_schema import BasePausableActionOutput
from app.core.agents.compliance_agent.models import EvidenceItem


class GithubPRAuditorAgentWithScreenshotDeps(BaseModel):
    goal: str = Field(
        ...,
        description="The goal of the auditor. Natural language description of what the user wants the agent to check ",
        examples="check if it has a priority label",
    )
    target_PR: str = Field(
        ...,
        description="GitHub URL",
        example="https://github.com/username/repo/pull/123",
    )
    github_token: str = Field(
        ...,
        description="GitHub access token for authentication",
        example="ghp_xxxxxxxxxxxxxxxxxxxx",
    )
    username: str = Field(
        ...,
        description="GitHub username",
        example="gavindh",
    )
    password: str = Field(
        ...,
        description="GitHub password",
        example="123456",
    )
    mfa_secret: str = Field(
        ...,
        description="GitHub MFA secret",
        example="123456",
    )
    pause_enabled: bool = Field(
        False,
        description="Whether to enable pause functionality",
        example=True,
    )


class GithubPRAuditorAgentWithScreenshotOutput(BasePausableActionOutput):
    is_passed: Literal["yes", "no"] = Field(
        ..., description="Whether the github auditor passed the check"
    )
    goal: str = Field(
        ...,
        description="The goal of the audit flow.",
    )
    reason: str = Field(
        ...,
        description="The reason for the github auditor to pass or fail the check. It should be detailed and concise",
    )
    feedback: str = Field(
        ...,
        description="Feedback about the github auditor process. Just a short summary of the reason",
    )
    evidence: List[EvidenceItem] = Field(
        ...,
        description="The evidence of the github auditor",
    )
    evidence_description: List[ScreenshotEvidence] = Field(
        ...,
        description="The description of the evidence",
    )


class GithubPRAuditorAgentWithScreenshotPauseOutput(
    GithubPRAuditorAgentWithScreenshotOutput
):
    pause_requested: Literal["yes", "no"] = Field(
        ..., description="Whether the agent is requesting a pause"
    )
    pause_reason: str = Field(
        ...,
        description="The reason for requesting a pause. It should be detailed and concise",
    )
