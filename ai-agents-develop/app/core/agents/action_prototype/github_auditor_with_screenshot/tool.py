import logfire
from alltrue.agents.schema.action_execution import PlainTextLog
from httpx import HTTPStatusError
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP

from app.core.agents.action_prototype.github_auditor_with_screenshot.schema import (
    GithubPRAuditorAgentWithScreenshotOutput,
    GithubPRAuditorAgentWithScreenshotPauseOutput,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot.tools.github_evidence_screenshot import (
    github_evidence_screenshot_tool,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot.tools.github_login import (
    github_login_tool,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

GITHUB_MCP_SERVER_URL = "https://api.githubcopilot.com/mcp/"


async def github_pr_auditor_with_screenshot(
    ctx: RunContext[ActionDeps],
    github_token: str,
    target_PR: str,
    goal: str,
    username: str,
    password: str,
    mfa_secret: str,
    pause_enabled: bool,
) -> (
    GithubPRAuditorAgentWithScreenshotOutput
    | GithubPRAuditorAgentWithScreenshotPauseOutput
):

    # attach the credentials to the action deps to avoid passing them by LLM
    ctx.deps.model_extra.update(
        {
            "username": username,
            "password": password,
            "mfa_secret": mfa_secret,
        }
    )

    try:
        github_mcp_server = MCPServerStreamableHTTP(
            url=GITHUB_MCP_SERVER_URL,
            headers={
                "Authorization": f"Bearer {github_token}",
            },
        )

        output_type = GithubPRAuditorAgentWithScreenshotOutput
        github_auditor_system_prompt = """
            You are a Github PR auditor and you will be given a github PR URL and a goal.
            You have to use the github_login tool to login to the github before using the github_evidence_screenshot tool.
            For the task you judge is compliant, you have to use the github_evidence_screenshot tool to take a screenshot as evidence.
        """
        if pause_enabled:
            output_type = GithubPRAuditorAgentWithScreenshotPauseOutput
            github_auditor_system_prompt += """
                If the github_login tool returns "successful": "no", or if you cannot proceed because of missing credentials
                (e.g., MFA secret not provided), you must immediately request a pause.
                Do not attempt any other tools after this.
            """

        agent = Agent(
            model=get_pydanticai_openai_llm(),
            toolsets=[github_mcp_server],
            tools=[github_login_tool, github_evidence_screenshot_tool],
            system_prompt=github_auditor_system_prompt,
        )
        try:
            result = await agent.run(
                f"""
                Check the PR: {target_PR}.
                The goal is: {goal}
            """,
                output_type=output_type,
                deps=ctx.deps,
            )
            logfire.info(f"GithubPRAuditorAgentWithScreenshotOutput: {result.output}")
        except HTTPStatusError as eg:
            for err in eg.exceptions:  # type: HTTPStatusError
                await ctx.deps.add_log(
                    PlainTextLog(
                        data=f"Unable to access Github server: Status code: {err.response.status_code}"
                    )
                )
            logfire.error(f"GithubPRAuditorAgent failed: {eg}")
            raise Exception("Unable to access Github server")

        logfire.info(f"GithubPRAuditorAgentWithScreenshotOutput: {result.output}")

        return result.output

    except Exception as e:
        logfire.error(f"GithubPRAuditorAgent failed: {e}")
        raise
