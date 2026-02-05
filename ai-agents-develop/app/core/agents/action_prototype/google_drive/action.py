import os
from pathlib import Path

import logfire
from alltrue.agents.schema.customer_credential import SecretStringCredentialModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import MCPServerStdio

from app.core.agents.action_prototype.google_drive.schema import GoogleDriveMCPOutput
from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.llm.model_registry import ModelRegistry
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json


async def find_and_download_previous_file(
    selected_model: str, instruction: str, google_token: str, working_dir: Path
) -> GoogleDriveMCPOutput:
    """
    Execute a Google Drive task instruction using an MCP server agent.
    Downloads files to the specified working directory based on the instruction.
    Returns the agent's output encapsulated in GoogleDriveMCPOutput.
    """

    logfire.info("Starting Google Drive MCP Server")
    refreshed_credentials_json = get_refreshed_credentials_json(google_token)
    server = MCPServerStdio(
        command="uv",
        args=["run", "python", "-m", "mcp_server.google_drive.server"],
        env={
            "GOOGLE_CREDENTIALS": refreshed_credentials_json,
            "WORKING_DIR": str(working_dir),
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
        timeout=30,
    )
    logfire.info("Google Drive MCP Server started")

    agent = Agent(
        model=ModelRegistry.get_pydantic_ai_llm(selected_model),
        toolsets=[server],
        output_type=GoogleDriveMCPOutput,
    )
    result = await agent.run(instruction)
    return result.output


async def google_drive_mcp_tool(
    ctx: RunContext[ToolActionDeps], instruction: str, google_token_name: str
):
    """
    Launch Google Drive MCP server and delegate the goal to a lightweight agent.

    Args:
        instruction: The instruction of the agent
        google_token_name: The name of the credential in the credentials
    """
    if google_token_name not in ctx.deps.credentials:
        raise ModelRetry(
            f"credential name '{google_token_name}' not found in credentials. Keys are: {ctx.deps.credentials.keys()}"
        )
    if isinstance(ctx.deps.credentials[google_token_name], SecretStringCredentialModel):
        google_token = ctx.deps.credentials[google_token_name].secret
    else:
        raise ModelRetry(f"credential '{google_token_name}' is not a token credential")
    download_dir = Path(ctx.deps.action_working_dir)
    download_helper_prompt = f"The output from mcp is stored in {download_dir}"
    return await find_and_download_previous_file(
        ctx.deps.selected_model,
        instruction + download_helper_prompt,
        google_token,
        download_dir,
    )
