from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.core.agents.compliance_agent.models import EvidenceItem


class GHCOAuditorDeps(BaseModel):
    target_business_unit: str = Field(
        ...,
        description="The business unit that the user wants the agent to check",
    )
    login_url: str = Field(
        ...,
        description="The URL of the GHCO login page",
    )
    navigation_instruction: str = Field(
        ...,
        description="The instructions for navigation to the page and download the files",
    )
    username: str = Field(
        ...,
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        description="Password",
    )
    report_instruction: str = Field(
        default="",
        description="Instructions for report generation including frequency and sample size mappings",
    )


class GHCOAuditorOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    successful: bool = Field(
        ...,
        description="Whether the GHCO auditor executed successfully",
    )
    reason: str = Field(
        ...,
        description="The reason for the GHCO auditor to pass or fail the check. It should be detailed and concise",
    )
    evidence: List[EvidenceItem] = Field(
        ...,
        description="The evidence of the GHCO auditor",
    )
