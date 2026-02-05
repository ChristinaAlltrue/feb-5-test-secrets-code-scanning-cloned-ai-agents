from typing import Optional

from pydantic import Field

from app.core.agents.action_prototype.audit_file_collection_agent.schema import (
    FileCollectionAgentNodeDeps,
    FileCollectionAgentOutput,
)


class AuditAnalysisConnectedNodeDeps(FileCollectionAgentNodeDeps):
    "Merge with AuditAnalysisAgentDeps by manually adding new dep from AuditAnalysisAgentDeps"

    user_list_instructions: str = Field(
        ...,
        description="Instructions for the audit analysis agent to generate user_list",
    )
    task_description: str = Field(
        ...,
        description="Description of the overall task for file collection",
    )


# class AuditAnalysisConnectedAgentDeps(FileCollectionAgentDeps):
#     # model_config = ConfigDict(extra="allow")
#     pass


class AuditAnalysisConnectedAgentOutput(FileCollectionAgentOutput):
    "Merge result on FileCollectionAgentOutput and AuditAnalysisAgentSimpleOutput"

    analysis_agent_feedback: str = Field(
        description="The response from the container agent",
    )
    analysis_agent_generated_file: Optional[str] = Field(
        description="The file path of the generated report file",
        default=None,
    )
    request_agent_downloaded_files: list[str] = Field(
        default_factory=list,
        description="The file paths for the downloaded files from request agent",
    )
