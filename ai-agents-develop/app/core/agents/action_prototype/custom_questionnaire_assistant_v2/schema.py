from typing import List, Literal

import pandas as pd
from pydantic import BaseModel, Field

from app.core.agents.compliance_agent.models import EvidenceItem
from app.core.graph.deps.action_deps import ActionDeps


# External node dependencies - what the outside world provides
class CustomQuestionnaireAssistantV2NodeDeps(BaseModel):
    google_token: str = Field(
        ...,
        description="The Google token to access the Google Drive",
        example="{'token': 'xxx', 'refresh_token': 'xxx', 'token_uri': 'xxx', 'client_id': 'xxx', 'client_secret': 'xxx', 'scopes': ['xxx'], 'universe_domain': 'xxx', 'account': 'xxx', 'expiry': 'xxx'}",
        repr=False,
    )
    # Node fields
    sheet_name: str = Field(
        ...,
        description="The sheet name of the file. It is the name of the sheet in the Google Sheets file.",
        examples="Sheet1",
    )
    context_document_name: str = Field(
        ...,
        description="The google document name that provides context for the agent to fill the spreadsheet.",
        example="company_policy",
    )
    goal: str = Field(
        ...,
        description="The goal of the agent. Natural language description of what the user wants the agent to do with the spreadsheet",
        example="Using the company policy document, fill in the spreadsheet with relevant information",
    )
    # model_config = ConfigDict(extra="allow")


# Internal agent dependencies - extends ActionDeps and adds node fields + DataFrame for tools
class CustomQuestionnaireAssistantV2AgentDeps(ActionDeps):
    model_config = {"arbitrary_types_allowed": True}

    # Node fields
    sheet_name: str = Field(
        ...,
        description="The sheet name of the file. It is the name of the sheet in the Google Sheets file.",
        examples="Sheet1",
    )
    context_document_name: str = Field(
        ...,
        description="The google document name that provides context for the agent to fill the spreadsheet.",
        example="company_policy",
    )
    goal: str = Field(
        ...,
        description="The goal of the agent. Natural language description of what the user wants the agent to do with the spreadsheet",
        example="Using the company policy document, fill in the spreadsheet with relevant information",
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


class CustomQuestionnaireAssistantV2Output(BaseModel):
    processed_result: LocalFileSaveResult = Field(
        ...,
        description="The path of the processed spreadsheet only",
    )
    evidence: List[EvidenceItem] = Field(
        ...,
        description="Evidence items containing file paths. Should include: 1) The modified spreadsheet file (processed_result.file_path), 2) The context document file. Use object_type='file' for both items.",
    )
