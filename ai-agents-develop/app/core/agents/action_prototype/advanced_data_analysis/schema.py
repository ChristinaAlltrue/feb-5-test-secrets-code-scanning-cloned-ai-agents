from pydantic import BaseModel, Field


class AdvancedDataAnalysisToolParams(BaseModel):
    task: str = Field(..., description="Detailed description of the data analysis task")
    file_names: list[str] = Field(
        default_factory=list,
        description="Names of previously downloaded files to process.",
    )
    process_files: bool = Field(
        False,
        description="Whether the tool should upload and process the provided files.",
    )
