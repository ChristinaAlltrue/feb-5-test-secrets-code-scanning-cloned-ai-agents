from pydantic import BaseModel, Field

from app.core.agents.base_action_schema.deps_schema import BaseActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput


class LongtermMemoryAgentDeps(BaseActionDeps):
    question: str = Field(
        ...,
        description="The question to ask the longterm memory agent",
        json_schema_extra={"example": "What evidence was submitted for the audit?"},
    )


class LongtermMemoryAgentOutput(BaseActionOutput):
    output: str = Field(
        ...,
        description="The answer from the longterm memory agent",
        json_schema_extra={
            "example": "Based on the documents, the evidence submitted includes..."
        },
    )


class LongtermMemoryAgentToolParams(BaseModel):
    question: str = Field(
        ..., description="The question to ask the longterm memory agent"
    )
