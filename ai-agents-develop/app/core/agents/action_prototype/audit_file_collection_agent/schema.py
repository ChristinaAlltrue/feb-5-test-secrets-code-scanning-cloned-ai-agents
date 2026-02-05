from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentDeps,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.updated_request_checker.schema_mixin import (
    FindAndDownloadDeps,
    GoogleTokenMixin,
)
from app.core.agents.compliance_agent.models import EvidenceItem


class FileCollectionAgentNodeDeps(BaseModel, GoogleTokenMixin):
    homepage_url: str = Field(
        ...,
        description="The homepage URL of the GHCO system",
    )
    username: str = Field(
        ...,
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        description="Password for authentication",
    )
    bu_contact: str = Field(
        ...,
        description="Business Unit contact person for the requests",
    )
    software_list: str = Field(
        ...,
        description="A string software applications to create requests for",
    )
    target_business_unit: str = Field(
        ...,
        description="The target business unit for the requests",
    )


class FileCollectionAgentDeps(
    GenericBrowserAgentDeps, FileCollectionAgentNodeDeps, FindAndDownloadDeps
):
    # model_config = ConfigDict(extra="allow")
    pass


class FileCollectionAgentOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    # should be always successful, otherwise would be paused
    # successful: bool = Field(
    #     ...,
    #     description="Whether all requests were created successfully",
    # )
    tracking_ids: List[str] = Field(
        default_factory=list,
        description="List of tracking IDs for the created requests",
    )
    softwares: List[str] = Field(
        default_factory=list,
        description="List of softwares being auditing",
    )
    requests_created: int = Field(
        default=0,
        description="Number of requests successfully created",
    )
    reason: str = Field(
        ...,
        description="Summary of request creation results and any issues encountered",
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence from the request creation process",
    )
