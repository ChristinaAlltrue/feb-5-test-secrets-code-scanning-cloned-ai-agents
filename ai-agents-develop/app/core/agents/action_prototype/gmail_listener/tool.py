import os
import pathlib

import logfire
from alltrue.agents.schema.action_execution import PlainTextLog
from httpx import HTTPStatusError
from pydantic import SecretStr
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio

from app.core.agents.action_prototype.gmail_listener.prompt import GMAIL_LISTENER_PROMPT
from app.core.agents.action_prototype.gmail_listener.schema import (
    GmailListenerAgentOutput,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json


async def gmail_listener(
    ctx: RunContext[ActionDeps],
    google_token: SecretStr,
    goal: str,
) -> GmailListenerAgentOutput:
    """
    Gmail Listener Agent that analyzes Gmail messages to determine if they match a specified goal.

    Args:
        ctx: RunContext containing action dependencies
        google_token: Google access token for Gmail authentication
        goal: Natural language description of what to look for in emails

    Returns:
        GmailListenerAgentOutput with trigger decision and feedback
    """
    try:
        # Create Gmail MCP server connection
        refreshed_credentials_json = get_refreshed_credentials_json(
            google_token.get_secret_value()
        )
        async with MCPServerStdio(
            command="uv",
            args=["run", "python", "-m", "mcp_server.gmail.server"],
            env={
                "GOOGLE_CREDENTIALS": refreshed_credentials_json,
                "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
                "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
                "WORKING_DIR": str(pathlib.Path(f"{ctx.deps.working_dir}").resolve()),
            },
        ) as gmail_mcp_server:

            # Create the agent with Gmail MCP server tools
            gmail_listener_agent = Agent(
                model=get_pydanticai_openai_llm("gpt-4.1-mini"),
                system_prompt=GMAIL_LISTENER_PROMPT,
                toolsets=[gmail_mcp_server],
            )

            try:
                # Run the agent with the goal
                result = await gmail_listener_agent.run(
                    f"""
                    Analyze Gmail messages to determine if they match this goal: {goal}

                    Please:
                    1. Search for relevant emails using appropriate Gmail search queries
                    2. Analyze the content of potentially relevant emails
                    3. Determine if any emails match the specified goal
                    4. Provide a clear decision (yes/no) and detailed feedback explaining your reasoning
                    """,
                    output_type=GmailListenerAgentOutput,
                    deps=ctx.deps,
                )

                await ctx.deps.add_log(
                    PlainTextLog(data="Successfully completed Gmail analysis")
                )

                return result.output

            except* HTTPStatusError as eg:
                for err in eg.exceptions:  # type: HTTPStatusError
                    await ctx.deps.add_log(
                        PlainTextLog(
                            data=f"Unable to access Gmail server: Status code: {err.response.status_code}"
                        )
                    )
                logfire.error(f"GmailListenerAgent failed: {eg}")
                raise Exception("Unable to access Gmail server")

    except Exception as e:
        await ctx.deps.add_log(PlainTextLog(data=f"Error: {str(e)}"))
        logfire.error(f"GmailListenerAgent failed: {e}")
        raise
