from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.agents.compliance_agent.models import EvidenceItem


class AuditAnalysisAgentDeps(BaseModel):
    report_instructions: str = Field(
        ...,
        description="Instructions for the audit analysis agent, should include audit requirements and report generation rules",
    )
    softwares: List[str] = Field(
        ...,
        description="List of softwares to analyze",
    )
    files_to_upload: Optional[List[str]] = Field(
        default=None,
        description="List of file paths to upload and analyze (supports Excel, PDF, images, text, logs, etc.)",
    )


class AuditAnalysisAgentOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    successful: bool = Field(
        ...,
        description="Whether the audit analysis agent executed successfully",
    )
    feedback: str = Field(
        ...,
        description="The response from the audit analysis agent execution",
    )
    generated_file: Optional[str] = Field(
        default=None,
        description="The file path of the generated audit report",
    )
    softwares_analyzed: List[str] = Field(
        default_factory=list,
        description="List of softwares that were analyzed",
    )
    files_processed: List[str] = Field(
        default_factory=list,
        description="List of files that were processed during analysis",
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence items from the audit analysis execution including the generated report",
    )
