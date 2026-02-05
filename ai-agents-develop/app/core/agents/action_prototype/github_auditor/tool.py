from typing import Any

import logfire
from alltrue.agents.schema.action_execution import PlainTextLog
from httpx import HTTPStatusError
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStreamableHTTP, ToolResult

from app.core.agents.action_prototype.github_auditor.schema import (
    GithubPRAuditorAgentOutput,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

GITHUB_MCP_SERVER_URL = "https://api.githubcopilot.com/mcp/"

from app.core.agents.utils.tool_call_log import tool_call_log_safe


async def process_tool_call(
    ctx: RunContext[ActionDeps],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    logs = []
    logs.append(
        PlainTextLog(data=f"Processing tool call: {name} with args: {tool_args}")
    )
    await tool_call_log_safe(ctx.deps.action_id, logs)
    return await call_tool(name, tool_args)


async def github_pr_auditor(
    ctx: RunContext[ActionDeps],
    github_token: str,
    target_PR: str,
    goal: str,
) -> GithubPRAuditorAgentOutput:

    try:
        server = MCPServerStreamableHTTP(
            url=GITHUB_MCP_SERVER_URL,
            headers={
                "Authorization": f"Bearer {github_token}",
            },
            process_tool_call=process_tool_call,
        )
        agent = Agent(
            model=get_pydanticai_openai_llm(),
            toolsets=[server],
        )
        try:
            result = await agent.run(
                f"""
                check the PR: {target_PR}.
                The goal is: {goal}
            """,
                output_type=GithubPRAuditorAgentOutput,
                deps=ctx.deps,
            )
            return result.output
        except* HTTPStatusError as eg:

            for err in eg.exceptions:  # type: HTTPStatusError
                await ctx.deps.add_log(
                    PlainTextLog(
                        data=f"Unable to access Github server: Status code: {err.response.status_code}"
                    )
                )
            logfire.error(f"GithubPRAuditorAgent failed: {eg}")
            raise Exception("Unable to access Github server")

    except Exception as e:
        logfire.error(f"GithubPRAuditorAgent failed: {e}")
        raise
