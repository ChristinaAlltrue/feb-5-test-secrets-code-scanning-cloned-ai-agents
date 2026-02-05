from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator
from pydantic_ai import BinaryContent


class CompliantModel(BaseModel):
    feedback: str = Field(
        description="The feedback of the compliance judgment. Should be short and concise."
    )
    reasoning: str = Field(
        description="The reasoning of the compliance judgment. Should be detailed and comprehensive."
    )
    non_compliant_evidence: List[str] = Field(
        default_factory=list,
        description="The evidence file path that is not compliant with the compliance rule. If there is no non-compliant evidence, return an empty list.",
    )
    compliant_evidence: List[str] = Field(
        default_factory=list,
        description="The evidence file path that is compliant with the compliance rule. If there is no compliant evidence, return an empty list.",
    )
    answer: Literal["COMPLIANT", "NON-COMPLIANT"]


class EvidenceItem(BaseModel):
    object_type: Literal["file"] = Field(
        description="The type of the evidence item",
    )
    path: str = Field(
        description="The path of the evidence item. It is a file path",
    )


class FileEvidence(BaseModel):
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    exists: bool
    is_file: bool
    readable: bool
    mime_type: str
    binary_content: BinaryContent
    description: str


class FileEvidenceError(BaseModel):
    error: str


FileEvidenceResult = Union[FileEvidence, FileEvidenceError]


class ResolvedEvidenceItem(BaseModel):
    """Model for resolved evidence items returned by data_resolver"""

    original_item: EvidenceItem
    resolved_data: FileEvidenceResult


class ComplianceInput(BaseModel):
    """Model for the input result structure passed to validate_compliance"""

    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined

    @model_validator(mode="before")
    @classmethod
    def drop_excluded(cls, values):
        """
        Drop unnecessary fields for compliance input. The execution_files are uploaded files in the file storage, should not be included in the compliance input.
        """
        for k in list(values.keys()):
            if k in {"execution_files"}:
                values.pop(k, None)
        return values


class UploadedFile(BaseModel):
    """Model for uploaded file information"""

    original_path: str = Field(description="Original file path")
    file_id: str = Field(description="File ID in the container")
    file_name: str = Field(description="File name")


class ReportGenerationResult(BaseModel):
    """Model for the result of report generation with evidence"""

    container_id: str = Field(description="Container ID where the report was generated")
    report_generated: bool = Field(
        description="Whether the report was successfully generated"
    )
    response_text: str = Field(
        description="Response text from the report generation (usually the filename)"
    )
    uploaded_files: List[UploadedFile] = Field(
        description="List of uploaded evidence files"
    )


class ContainerFile(BaseModel):
    """Model for files in a container"""

    id: str = Field(description="File ID in the container")
    name: str = Field(description="File name")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    created_at: Optional[int] = Field(
        default=None, description="File creation timestamp"
    )

    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined
