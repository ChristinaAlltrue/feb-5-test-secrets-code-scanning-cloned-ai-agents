from enum import Enum
from pathlib import Path
from typing import Optional

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from app.core.agents.action_prototype.auth_agents.authentication_agent import (
    create_auth_status_agent,
    create_authenticated_session_with_agents,
)
from app.core.agents.action_prototype.browser_tool.action import process_tool_call
from app.core.agents.action_prototype.generic_browser_agent.schema import (
    ActionDeps,
    GenericBrowserAgentDeps,
    GenericBrowserAgentOutput,
)
from app.core.agents.action_prototype.utils import (
    detect_tool_call_loop_processor,
    limit_browser_tool_call_history_processor,
    trim_page_snapshots_processor,
)
from app.core.agents.utils.browser_utils.file_processing import process_downloaded_files
from app.core.llm.pydanticai.gemini_model import get_pydanticai_gemini_llm  # noqa: F401
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm  # noqa: F401


async def is_session_authenticated(storage_state_path: Path, test_url: str) -> bool:
    """Check if the stored session is still valid using authentication agent"""
    if not storage_state_path.exists():
        return False

    try:
        # Use the authentication agent to check status
        auth_result = await create_auth_status_agent(
            test_url=test_url, storage_state_path=storage_state_path, headless=True
        )

        return auth_result.is_authenticated == "yes"

    except Exception:
        return False


async def create_authenticated_session(
    storage_state_path: Path,
    username: str,
    password: str,
    login_url: str,
    test_url: str,
    headless: bool = True,
):
    """Create authenticated session using dynamic element detection agents"""

    print("Creating authenticated session with dynamic element detection...")

    # Ensure the storage state directory exists
    storage_state_path.parent.mkdir(parents=True, exist_ok=True)

    # Use the agent-based authentication system
    auth_result = await create_authenticated_session_with_agents(
        login_url=login_url,
        test_url=test_url,
        username=username,
        password=password,
        storage_state_path=storage_state_path,
        headless=headless,
    )

    if auth_result.is_authenticated != "yes":
        raise ValueError(
            f"Failed to create authenticated session using agents: {auth_result.feedback}"
        )

    print(f"Authentication state saved to {storage_state_path}")
    return str(storage_state_path)


class ServerMode(str, Enum):
    EXTERNAL = "external"
    DIRECT = "direct"


class TaskDifficulty(str, Enum):
    SIMPLE = "simple"
    HARD = "hard"


DEFAULT_MODEL = "gemini-2.5-pro"
DIFFICULTY_MODEL_MAP = {
    TaskDifficulty.SIMPLE: "gemini-2.5-flash",
    TaskDifficulty.HARD: "gemini-2.5-pro",
}


async def generic_browser_agent_playwright(
    ctx: RunContext[GenericBrowserAgentDeps],
    task: str,
    start_url: str,
    model_name: str = DEFAULT_MODEL,
    server_mode: ServerMode = ServerMode.DIRECT,
    mcp_server_url: str = "http://localhost:8931/mcp",
    external_downloads_path: Optional[str] = "playwright/files",
    **_,
) -> GenericBrowserAgentOutput:
    """
    Playwright implementation that supports both external MCP server and direct MCP server modes.

    Args:
        server_mode: EXTERNAL uses MCPServerStreamableHTTP (for development only), DIRECT uses MCPServerStdio
        mcp_server_url: URL for external MCP server (only used in EXTERNAL mode)
        external_downloads_path: Path where external MCP server downloads files (only used in EXTERNAL mode, should match --output-dir)
    """

    mode_name = (
        "External MCP Server"
        if server_mode == ServerMode.EXTERNAL
        else "Direct MCP Server"
    )
    logfire.info(f"Starting Generic Browser Agent (Playwright with {mode_name})")
    logfire.info(f"Task: {task}")

    deps = ctx.deps
    # Set up directories
    browser_deps = deps.get_browser_deps()
    if not browser_deps:
        logfire.info("Initializing browser dependencies...")
        deps.init_browser_deps()
        browser_deps = deps.get_browser_deps()
        assert (
            browser_deps is not None
        ), "browser_deps is still None after initialization"

    # Use external downloads path for EXTERNAL mode, default to browser deps path
    if server_mode == ServerMode.EXTERNAL:
        assert (
            external_downloads_path
        ), "external_downloads_path is required when using EXTERNAL server mode"
        downloads_path = external_downloads_path
    elif server_mode == ServerMode.DIRECT:
        downloads_path = browser_deps.download_path
        assert "storage_state_path" in vars(ctx.deps), "storage_state_path not in deps"
    else:
        raise ValueError(f"Unknown server_mode: {server_mode}")

    assert (
        ctx.deps.working_dir is not None
    ), "ctx.deps.working_dir is None, cannot process files"

    try:
        # Authentication and storage state only needed for DIRECT mode
        if server_mode == ServerMode.DIRECT:
            deps_validated = GenericBrowserAgentDeps.model_validate(vars(ctx.deps))
            storage_state_path = Path(deps_validated.storage_state_path)

            # Ensure storage state directory exists
            storage_state_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if authentication is valid
            if not await is_session_authenticated(storage_state_path, start_url):
                logfire.info(
                    f"No valid authentication found. Creating authenticated session..."
                )
                try:
                    # Get credentials from context
                    username = ctx.deps.username
                    password = ctx.deps.password

                    await create_authenticated_session(
                        storage_state_path=storage_state_path,
                        username=username,
                        password=password,
                        login_url=start_url,  # Let the target URL redirect to login
                        test_url=start_url,  # Use target URL for testing authentication
                    )
                    logfire.info("Authentication session created successfully")
                except Exception as e:
                    logfire.error(f"Failed to create authentication session: {e}")
                    raise
            else:
                logfire.info(
                    f"Using existing valid authentication from {storage_state_path}"
                )

        # Create MCP server based on mode
        if server_mode == ServerMode.EXTERNAL:
            # Use external MCP server
            server = MCPServerStreamableHTTP(
                url=mcp_server_url, max_retries=5, process_tool_call=process_tool_call
            )
        else:
            # Use direct MCP server (spawns the server process)
            server = MCPServerStdio(
                "npx",
                args=[
                    "@playwright/mcp@0.0.41",
                    "--storage-state",
                    str(storage_state_path),
                    "--isolated",
                    "--no-sandbox",
                    "--headless",
                    "--output-dir",
                    str(downloads_path),
                    "--viewport-size",
                    "1380,1000",
                ],
                timeout=30,
                max_retries=5,
                process_tool_call=process_tool_call,
            )

        # Create Pydantic AI agent with Playwright MCP integration
        agent = Agent(
            model=get_pydanticai_gemini_llm(model_name=model_name, timeout_ms=30_000),
            # model=get_pydanticai_openai_llm(model_name=model_name),
            model_settings=ModelSettings(
                temperature=0, parallel_tool_calls=False
            ),  # not all model support the param parallel_tool_calls
            toolsets=[server],
            output_type=GenericBrowserAgentOutput,
            system_prompt=f"""You are a web automation assistant using Playwright tools, which has a Auto-wait feature. You should check the tool response carefully after each action to decide the next step. You need to complete the assigned task at your best.

## Starting Context
The browser session is authenticated for: {start_url}
Unless the task specifies a different URL, you should start your work at this URL.

## File Download Protocol
When downloading files:
1. Track all downloaded filenames in the "files" array
2. Download only files directly relevant to the current task

## Error Handling (e.g. TimeoutError)
- If an action fails, retry at least once and attempt at least two alternative approach before reporting failure
- If a browser_click fails, attempt to click its parent elements even though they may not be a button, this often resolves issues with nested interactive elements

## Context Management
- Browser tool calls older than 10 steps are removed from history
- Always use fresh page snapshots to understand current state rather than relying on historical tool responses
- Make decisions based on the most recent snapshot and tool results

## UI Interaction Guidelines

### Input Fields
- **Non-standard inputs**: Some input fields are `<div>` elements with contenteditable attributes
- Click these elements first to focus them before typing

### Action Pacing
- Execute **one action per step** to prevent race conditions and crashes
- Wait for each action to complete before proceeding

### File Upload Actions
1. Get the latest page snapshot
2. Use browser_click successfully with the content of tool result containing: "### Modal state
- [File chooser]: can be handled by the "browser_file_upload" tool". When you cannot see this content, you need to try to click its *parent element*
3. Then use the browser_file_upload tool to upload files
4. Otherwise, you should never call the browser_file_upload tool

### Dynamic Content
- Pages may update asynchronously after interactions
- Always capture a fresh snapshot after UI interactions to see the current state

""",
            deps_type=ActionDeps,
            history_processors=[
                detect_tool_call_loop_processor,
                limit_browser_tool_call_history_processor,
                trim_page_snapshots_processor,
            ],
        )

        # # Add custom verify_downloaded_files tool
        # # NOTE: Download behavior varies by server mode:
        # # - DIRECT mode: files downloaded to configured output directory
        # # - EXTERNAL mode: files downloaded to server's fixed directory
        # @agent.tool_plain
        # async def verify_downloaded_files(filename: str) -> str:
        #     """Verify if a specific file has been downloaded to the downloads directory"""
        #     download_dir = Path(downloads_path)
        #     file_path = download_dir / filename

        #     if file_path.exists() and file_path.is_file():
        #         logfire.info(
        #             f"Generic Browser Agent ({mode_name}) > File verified: {filename}"
        #         )
        #         return f"File '{filename}' has been successfully downloaded"
        #     else:
        #         # List available files for debugging
        #         available_files = []
        #         if download_dir.exists():
        #             for file in download_dir.iterdir():
        #                 if file.is_file():
        #                     available_files.append(file.name)

        #         logfire.info(
        #             f"Generic Browser Agent ({mode_name}) > File not found: {filename}. Available files: {available_files}"
        #         )
        #         return (
        #             f"File '{filename}' not found. Available files: {available_files}"
        #         )

        # Run the agent task
        async with agent:
            with logfire.span(f"playwright_{server_mode.lower()}_agent_task"):
                result = await agent.run(
                    task,
                    deps=ActionDeps(**vars(ctx.deps)),
                    usage_limits=UsageLimits(request_limit=70),
                )

                # Log the agent's output
                await ctx.deps.add_log(
                    PlainTextLog(data=f"Agent response: {result.output}")
                )

                parsed_result = result.output

    except Exception as e:
        logfire.error(f"Error in {mode_name} browser agent: {e}")
        await ctx.deps.add_log(PlainTextLog(data=f"Browser agent error: {str(e)}"))

        parsed_result = GenericBrowserAgentOutput(
            successful="no",
            feedback=f"Browser agent failed with error: {str(e)}",
            execution_flow="Agent execution failed with exception",
        )

    # if parsed_result.successful == "no":
    #     raise ValueError(
    #         f"Generic browser agent failed to finish the task: {parsed_result.feedback}"
    #     )

    # Post-process files if any were downloaded
    if parsed_result.files:
        parsed_result.files = process_downloaded_files(
            parsed_result.files, raise_on_missing=True
        )

    logfire.info(
        f"Generic browser agent ({mode_name}) execution result: {parsed_result}"
    )
    await ctx.deps.add_log(ObjectLog(data=parsed_result.model_dump()))

    return parsed_result


async def generic_browser_agent_playwright_for_llm(
    ctx: RunContext[GenericBrowserAgentDeps],
    task: str,
    start_url: str,
    difficulty: TaskDifficulty = TaskDifficulty.HARD,
) -> GenericBrowserAgentOutput:
    """
    Execute browser automation tasks with automatic model selection based on task difficulty.

    This is a simplified wrapper around generic_browser_agent_playwright designed for LLM tool use.
    It automatically selects the appropriate model based on task complexity:
    - SIMPLE tasks use a faster model optimized for straightforward interactions
    - HARD tasks use a more capable model for complex workflows

    The agent handles authentication automatically, uses Playwright for browser control via MCP,
    and returns structured output including success status, execution flow, and downloaded files.

    Args:
        ctx: Runtime context containing dependencies like credentials and working directory
        task: Natural language description of the browser automation task to perform
        start_url: The starting URL for the browser session (used for authentication and initial navigation)
        difficulty: Task complexity level (SIMPLE or HARD). Defaults to HARD for better reliability.

    Returns:
        GenericBrowserAgentOutput containing:
            - successful: "yes" or "no" indicating task completion
            - feedback: Natural language description of results
            - execution_flow: Step-by-step execution summary
            - data: Optional structured data extracted during task
            - files: Optional list of downloaded file paths

    Example:
        Use SIMPLE for basic navigation and data extraction:
        - "Navigate to the homepage and extract the title"
        - "Click the login button and verify the form appears"

        Use HARD for complex multi-step workflows:
        - "Fill out a multi-page form with validation handling"
        - "Navigate through nested menus and extract dynamic table data"
    """

    try:
        # Map difficulty to model
        model_name = DIFFICULTY_MODEL_MAP[difficulty]

        return await generic_browser_agent_playwright(
            ctx=ctx,
            task=task,
            start_url=start_url,
            model_name=model_name,
        )
    except Exception as e:
        logfire.error(f"Error in generic_browser_agent_playwright_for_llm: {e}")
        await ctx.deps.add_log(PlainTextLog(data=f"Browser agent error: {str(e)}"))

        raise ModelRetry(
            f"generic_browser_agent_playwright_for_llm failed with error: {str(e)}"
        ) from e


# Export the tools
generic_browser_agent_playwright_tool = Tool(
    generic_browser_agent_playwright_for_llm,
    takes_ctx=True,
    name="browser_agent",
)
