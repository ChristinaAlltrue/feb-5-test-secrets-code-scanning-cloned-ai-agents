import os
import pathlib

from pydantic import BaseModel, Field, SecretStr
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.mcp import MCPServerStdio

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json

from .schema_mixin import FindAndDownloadDeps


class DownloadedFileOutput(BaseModel):
    file_path: list[str] = Field(..., description="The path to the downloaded file")


async def find_and_download_previous_file(
    instruction: str, google_credentials: SecretStr, working_dir: pathlib.Path
) -> DownloadedFileOutput:
    """
    Determine which of the given request IDs have updates.
    Respond ONLY with a JSON object of shape: {"updated_request_ids": [string]}.
    If none are updated, return {"updated_request_ids": []}.
    """
    refreshed_credentials_json = get_refreshed_credentials_json(
        google_credentials.get_secret_value()
    )
    server = MCPServerStdio(
        command="uv",
        args=["run", "python", "-m", "mcp_server.google_drive.server"],
        env={
            "GOOGLE_CREDENTIALS": refreshed_credentials_json,
            "WORKING_DIR": str(working_dir),
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
    )

    agent = Agent(
        model=get_pydanticai_openai_llm(),
        toolsets=[server],
        output_type=DownloadedFileOutput,
    )
    result = await agent.run(instruction)
    return result.output


async def find_and_download_previous_file_with_ctx(
    ctx: RunContext[FindAndDownloadDeps], instruction: str
):
    if ctx.deps.working_dir is None:
        raise ValueError(f"ctx.deps.working_dir is None")

    return await find_and_download_previous_file(
        instruction, ctx.deps.google_token, pathlib.Path(ctx.deps.working_dir)
    )


find_and_download_previous_file_tool = Tool(
    find_and_download_previous_file_with_ctx,
    takes_ctx=True,
    name="find_and_download_previous_file",
)
