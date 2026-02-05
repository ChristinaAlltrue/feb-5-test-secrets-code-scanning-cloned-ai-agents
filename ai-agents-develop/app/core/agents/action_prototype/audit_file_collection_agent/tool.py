from datetime import datetime, timedelta

import logfire
from pydantic import SecretStr
from pydantic_ai import Agent, Tool
from pydantic_ai.mcp import MCPServerStdio
from pydantic_graph import GraphRunContext

from app.core.agents.action_prototype.audit_file_collection_agent.prompt import (
    FILE_COLLECTION_AGENT_PROMPT,
)
from app.core.agents.action_prototype.audit_file_collection_agent.schema import (
    FileCollectionAgentDeps,
    FileCollectionAgentOutput,
)
from app.core.agents.action_prototype.generic_browser_agent.generic_browser_agent_playwright import (
    generic_browser_agent_playwright_tool,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.updated_request_checker.find_and_download_previous_file import (
    find_and_download_previous_file_tool,
)
from app.core.agents.utils.action_utils import run_agent_with_history
from app.core.agents.utils.storage_utils import generate_storage_state_path
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from app.exceptions.control_exceptions import PauseExecution
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json


def trigger_pause(
    reason: str = "Waiting for Business Unit to submit required files",
) -> str:
    """Trigger pause to wait for any external action, e.g. BU to submit files"""

    logfire.info(f"Triggering pause in FileCollectionAgent: {reason}")

    raise PauseExecution(
        {
            "reason": reason,
            "agent": "FileCollectionAgent",
        }
    )


def get_date_after_days(days: int) -> str:
    """Calculate and return the date that is d days after today in MM/DD/YYYY format"""
    today = datetime.now()
    target_date = today + timedelta(days=days)
    return target_date.strftime("%m/%d/%Y")


def gmail_toolset(deps: FileCollectionAgentDeps):
    refreshed_credentials_json = get_refreshed_credentials_json(
        deps.google_token.get_secret_value()
    )
    return MCPServerStdio(
        command="uv",
        args=["run", "python", "-m", "mcp_server.gmail.server"],
        env={
            "GOOGLE_CREDENTIALS": refreshed_credentials_json,
        },
    )


FILE_COLLECTION_AGENT = Agent(
    model=get_pydanticai_openai_llm(),
    deps_type=FileCollectionAgentDeps,
    system_prompt=FILE_COLLECTION_AGENT_PROMPT,
    output_type=FileCollectionAgentOutput,
    # toolsets=[gmail_toolset],  # unable to define here due to context problem, error: RuntimeError: Attempted to exit cancel scope in a different task than it was entered in, probably due to some initialization and clean up problem in Pydantic AI
    tools=[
        generic_browser_agent_playwright_tool,
        Tool(trigger_pause, takes_ctx=False),
        # check_request_update_tool,
        find_and_download_previous_file_tool,
        get_date_after_days,
    ],
)


async def run_file_collection_agent(
    ctx: GraphRunContext[State, GraphDeps],
    task_description: str,
    homepage_url: str,
    username: str,
    password: str,
    bu_contact: str,
    software_list_string: str,
    target_business_unit: str,
    google_token: SecretStr,
) -> FileCollectionAgentOutput:
    """Main function to run the File Collection Agent"""

    prompt = f"""Configuration:
    - homepage_url: {homepage_url}
    - bu_contact: {bu_contact}
    - target_business_unit: {target_business_unit}
    - Software list: {software_list_string}

    {task_description}
    """

    storage_state_path = generate_storage_state_path(homepage_url, username, password)

    deps = FileCollectionAgentDeps(
        **vars(ctx.deps),
        **{
            "homepage_url": homepage_url,
            "username": username,
            "password": password,
            "bu_contact": bu_contact,
            "software_list": software_list_string,
            "target_business_unit": target_business_unit,
            "storage_state_path": storage_state_path,
            "google_token": google_token,
        },
    )

    logfire.info("Starting File Collection Agent")

    # Set up directories
    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()

    try:
        # Use run_agent_with_history to automatically save/restore message history for pause/resume
        result = await run_agent_with_history(
            FILE_COLLECTION_AGENT,
            prompt,
            deps,
            ctx,
            use_history=True,
            toolsets=[gmail_toolset(deps)],
        )
        return result.output
    except PauseExecution as pause_exc:
        raise pause_exc
