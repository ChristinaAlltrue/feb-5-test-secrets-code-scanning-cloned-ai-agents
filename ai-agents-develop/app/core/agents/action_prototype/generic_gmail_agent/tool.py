import os
import pathlib
from typing import Any

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from alltrue.agents.schema.customer_credential import SecretStringCredentialModel
from httpx import HTTPStatusError
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult

from app.core.agents.utils.tool_call_log import tool_call_log_safe
from app.core.graph.deps.action_deps import ActionDeps, ToolActionDeps
from app.core.llm.model_registry import ModelRegistry
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json


async def process_tool_call(
    ctx: RunContext[ActionDeps],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""

    def prettify_tool_name(name: str) -> str:
        return name.replace("_", " ").capitalize()

    def scrub_sensitive_info(args: dict) -> dict:
        res = {}
        for k, v in args.items():
            if "token" in k:
                res[k] = "<token>"
            else:
                res[k] = v
        return res

    logs = [
        PlainTextLog(data=f"Processing tool call: {prettify_tool_name(name)}"),
        ObjectLog(data=scrub_sensitive_info(tool_args)),
    ]

    await tool_call_log_safe(ctx.deps.action_id, logs)
    return await call_tool(name, tool_args)


async def generic_gmail_agent_tool(
    ctx: RunContext[ToolActionDeps],
    goal: str,
    google_token_key_name: str,
) -> str:
    """
    Launch Gmail MCP server and delegate the goal to a lightweight agent.

    Args:
        goal: The goal of the agent
        google_token_key_name: The key name of the token in the credentials
    """
    if google_token_key_name not in ctx.deps.credentials:
        raise ModelRetry(
            f"credential name '{google_token_key_name}' not found in credentials. Keys are: {ctx.deps.credentials.keys()}"
        )
    if isinstance(
        ctx.deps.credentials[google_token_key_name], SecretStringCredentialModel
    ):
        google_token = ctx.deps.credentials[google_token_key_name].secret
    else:
        raise ModelRetry(
            f"credential '{google_token_key_name}' is not a token credential"
        )

    try:
        logfire.info("Starting Gmail MCP Server")
        # Start Gmail MCP Server using provided token
        refreshed_credentials_json = get_refreshed_credentials_json(google_token)
        async with MCPServerStdio(
            command="uv",
            args=["run", "python", "-m", "mcp_server.gmail.server"],
            env={
                "GOOGLE_CREDENTIALS": refreshed_credentials_json,
                "LOGFIRE_TOKEN": os.environ.get("LOGFIRE_TOKEN", ""),
                "LOGFIRE_SERVICE_NAME": os.environ.get(
                    "LOGFIRE_SERVICE_NAME", "ai-agents"
                ),
                "WORKING_DIR": str(pathlib.Path(f"{ctx.deps.working_dir}").resolve()),
            },
            process_tool_call=process_tool_call,
            timeout=30,
        ) as gmail_mcp_server:
            logfire.info("Gmail MCP Server started")

            agent = Agent(
                model=ModelRegistry.get_pydantic_ai_llm(ctx.deps.selected_model),
                toolsets=[gmail_mcp_server],
            )

            try:
                result = await agent.run(
                    user_prompt=goal, output_type=str, deps=ctx.deps
                )
                return result.output
            except* HTTPStatusError as eg:
                for err in eg.exceptions:  # type: ignore[attr-defined]
                    logfire.error(f"GmailAgent HTTP error: {err}")
                raise Exception("Unable to access Gmail MCP server")

    except Exception as e:
        logfire.error(f"generic_gmail_agent_tool failed: {e}")
        raise
