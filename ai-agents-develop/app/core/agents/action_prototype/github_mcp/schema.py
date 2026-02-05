from pydantic import BaseModel, Field


class GithubMCPToolParams(BaseModel):
    task_description: str = Field(
        ..., description="Detailed description of the Github MCP task to be performed."
    )
    github_token: str = Field(
        ...,
        description="GitHub token with necessary permissions to access repositories.",
    )
