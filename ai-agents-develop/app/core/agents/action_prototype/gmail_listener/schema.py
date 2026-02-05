from typing import Literal

from pydantic import BaseModel, Field, SecretStr


# Complete parameters and it depends on the caller where they come from either from the action instance or the entity instance.
class GmailListenerAgentDeps(BaseModel):
    goal: str = Field(
        ...,
        description="The goal of the Gmail listener. Natural language description of what the user wants the agent to check in emails",
        examples="is there any email related with evidence update",
    )
    google_token: SecretStr = Field(
        ...,
        description="Google access token for Gmail authentication",
        example="ya29.xxxxxxxxxxxxxxxxxxxx",
    )


class GmailListenerAgentOutput(BaseModel):
    trigger: Literal["yes", "no"] = Field(
        ..., description="Whether the Gmail listener should trigger based on the goal"
    )
    feedback: str = Field(
        ...,
        description="The reason for the Gmail listener decision. It should be detailed and concise with the email content and the reason for the decision",
    )
