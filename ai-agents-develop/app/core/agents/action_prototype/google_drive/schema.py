from pydantic import BaseModel, Field


class GoogleDriveMCPOutput(BaseModel):

    output: str = Field(..., description="The output from the Google Drive MCP tool")


class GoogleDriveMCPParams(BaseModel):
    instruction: str = Field(
        ..., description="The instruction for the Google Drive MCP tool"
    )
    google_token: str = Field(
        ...,
        description="""The google_token is the key name of the credentials you have provided to access Google Drive. It would be like '{"token": "token_value}' The tool accepts the whole string '{"token": "token_value}'""",
    )
