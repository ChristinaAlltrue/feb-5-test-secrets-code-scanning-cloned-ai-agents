from typing import Literal

from pydantic import BaseModel, Field


class BaseActionOutput(BaseModel):
    successful: Literal["yes", "no"] = Field(
        ..., description="Whether the action was successful"
    )
    feedback: str = Field(
        ...,
        description="Feedback about the action process",
    )


class BasePausableActionOutput(BaseActionOutput):
    pause: Literal["yes", "no"] = Field(
        default="no",
        description="Whether the agent is requesting a pause",
    )
    pause_reason: str = Field(
        description="The reason for requesting a pause. It should be detailed and concise. Can be empty if no pause is requested",
    )
