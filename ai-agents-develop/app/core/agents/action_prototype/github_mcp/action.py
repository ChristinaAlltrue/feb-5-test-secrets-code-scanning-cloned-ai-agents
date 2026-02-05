import traceback

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP

from app.core.agents.action_prototype.github_mcp.prompt import GITHUB_MCP_SYSTEM_PROMPT
from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.llm.model_registry import ModelRegistry

GITHUB_MCP_SERVER_URL = "https://api.githubcopilot.com/mcp/"


async def github_mcp_tool(
    ctx: RunContext[ToolActionDeps],
    task_description: str,
    github_token: str,
):
    await ctx.deps.add_log(
        PlainTextLog(data="Starting Github MCP Tool"),
    )
    logfire.info(f"Task -> GithubMCP: {task_description}")

    try:
        logfire.info(
            f"Using model: {ctx.deps.selected_model}"
        )  # Directly use the model passed by the LLM

        github_mcp_server = MCPServerStreamableHTTP(
            url=GITHUB_MCP_SERVER_URL,
            headers={
                "Authorization": f"Bearer {github_token}",
            },
        )
        agent = Agent(
            model=ModelRegistry.get_pydantic_ai_llm(ctx.deps.selected_model),
            toolsets=[github_mcp_server],
            system_prompt=GITHUB_MCP_SYSTEM_PROMPT,
        )

        result = await agent.run(
            user_prompt=task_description,
            output_type=str,
            deps=ctx.deps,
        )

        logfire.info(f"Github MCP: {result.output}")
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Github MCP Agent workflow completed"),
                ObjectLog(data=result.output),
            ]
        )
        return result.output

    except Exception as e:
        logfire.trace(f"Github MCP Agent failed: {e}")
        error_msg = f"Github MCP Agent failed: {e}"
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Github MCP Agent workflow failed"),
                ObjectLog(data={"error": str(e)}),
            ]
        )
        traceback.print_exc()
        raise
