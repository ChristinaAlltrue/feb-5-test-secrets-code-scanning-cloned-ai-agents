from typing import Literal

from pydantic import BaseModel, Field


# Complete parameters and it depends on the caller where they come from either from the action instance or the entity instance.
class GithubPRAuditorAgentDeps(BaseModel):
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


class GithubPRAuditorAgentOutput(BaseModel):
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
