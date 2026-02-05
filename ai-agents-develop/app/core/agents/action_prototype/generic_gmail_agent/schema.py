from pydantic import BaseModel, Field, SecretStr

from app.core.agents.base_action_schema.deps_schema import BaseCredentialActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput


class GenericGmailAgentDeps(BaseCredentialActionDeps):
    goal: str = Field(
        ...,
        description="What do you want the Gmail agent to do",
        json_schema_extra={"example": "Send a status update email to the team"},
    )
    expected_output: str = Field(
        ...,
        description="What the output should include",
        json_schema_extra={
            "example": "Email subject, recipients, and send confirmation"
        },
    )


class GenericGmailAgentOutput(BaseActionOutput):
    output: str = Field(
        ...,
        description="Raw output from the Gmail agent",
        json_schema_extra={
            "example": "Email sent to user@example.com with subject 'Update'"
        },
    )


class GenericGmailAgentToolParams(BaseModel):
    goal: str = Field(..., description="What do you want the Gmail agent to do")
    google_token: SecretStr = Field(
        ..., description="Google credentials token to start the MCP server"
    )
