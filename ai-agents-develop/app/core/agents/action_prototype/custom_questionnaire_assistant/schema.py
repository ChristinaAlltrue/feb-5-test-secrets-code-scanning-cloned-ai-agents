from typing import List, Literal

import pandas as pd
from pydantic import BaseModel, Field

from app.core.agents.compliance_agent.models import EvidenceItem
from app.core.graph.deps.action_deps import ActionDeps


# External node dependencies - what the outside world provides
class CustomQuestionnaireAssistantNodeDeps(BaseModel):
    sheet_url: str = Field(
        ...,
        description="The sheet url of the .xlsx file. The url is expected to be a public url that can be accessed without authentication",
    )
    context_document_url: str = Field(
        ...,
        description="Document url that provides context for the agent to fill the spreadsheet. The url is expected to be a public url that can be accessed without authentication",
    )
    goal: str = Field(...)
    # model_config = ConfigDict(extra="allow")


# Internal agent dependencies - extends ActionDeps and adds node fields + DataFrame for tools
class CustomQuestionnaireAssistantAgentDeps(ActionDeps):
    model_config = {"arbitrary_types_allowed": True}

    # Node fields
    sheet_url: str = Field(
        ...,
        description="The sheet url of the .xlsx file. The url is expected to be a public url that can be accessed without authentication",
    )
    context_document_url: str = Field(
        ...,
        description="Document url that provides context for the agent to fill the spreadsheet. The url is expected to be a public url that can be accessed without authentication",
    )
    goal: str = Field(
        ...,
        description="The goal of the agent. Natural language description of what the user wants the agent to do with the spreadsheet",
    )

    # Tool fields
    original_dataframe: pd.DataFrame | None = Field(
        default=None,
        description="The original DataFrame containing the spreadsheet data",
        repr=False,
        exclude=True,
    )
    context_content: str = Field(
        default="",
        description="The content of the context document",
        repr=False,
    )


class LocalFileSaveResult(BaseModel):
    type: Literal["local"] = "local"
    file_name: str
    file_path: str


class ProcessingResult(BaseModel):
    """Result of processing the spreadsheet with context document."""

    modified_spreadsheet: LocalFileSaveResult = Field(
        ..., description="Information about the saved modified spreadsheet file"
    )
    context_document: LocalFileSaveResult = Field(
        ..., description="Information about the saved context document file"
    )
    questions_answered: int = Field(
        ..., description="Number of questions answered in the spreadsheet"
    )
    total_rows: int = Field(..., description="Total number of rows in the spreadsheet")


class CustomQuestionnaireAssistantOutput(BaseModel):
    processed_result: LocalFileSaveResult = Field(
        ...,
        description="The path of the processed spreadsheet only",
    )
    evidence: List[EvidenceItem] = Field(
        ...,
        description="Evidence items containing file paths. Should include: 1) The modified spreadsheet file (processed_result.file_path), 2) The context document file. Use object_type='file' for both items.",
    )
