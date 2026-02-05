from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.agents.base_action_schema.output_schema import BasePausableActionOutput


class ToolConfiguration(BaseModel):
    tool_id: str = Field(
        ..., description="ID of the tool, matched against TOOLS_REGISTRY keys."
    )
    selected_model: Optional[str] = Field(
        default=None,
        description="The specific model ID to use for this tool. If None, the system's default or framework-level selected model will be used.",
    )


class SupervisorAgentDeps(BaseModel):
    model_config = ConfigDict(extra="ignore")

    task_description: str = Field(
        ..., description="Primary task the agent should accomplish"
    )
    additional_description: str = Field(
        ..., description="Additional context or requirements for the output"
    )
    tools: List[ToolConfiguration] = Field(
        default_factory=list,
        description="List of tool configurations to include for the agent",
    )
    model_provider: Literal["openai", "gemini"] = Field(
        default="openai",
        description="The model provider to use for the agent",
    )
    model_name: str = Field(
        default="gpt-5.1",
        description="The model name to use for the agent",
    )
    selected_model: Optional[str] = Field(
        default=None,
        description="The specific model ID to use for the agent, overriding model_name if provided.",
    )


class SupervisorOutput(BasePausableActionOutput):
    output: str = Field(
        ..., description="Final textual output from the agent execution"
    )
