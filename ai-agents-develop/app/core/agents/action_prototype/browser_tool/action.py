import socket
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

import logfire
from alltrue.agents.schema.action_execution import (
    ObjectLog,
    PlainTextLog,
    S3ScreenshotLog,
)
from alltrue.agents.schema.customer_credential import LoginCredentialModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import (
    CallToolFunc,
    MCPServerStdio,
    MCPServerStreamableHTTP,
    ToolResult,
)
from pydantic_ai.messages import BinaryContent
from pydantic_ai.usage import UsageLimits

from app.core.agents.action_prototype.auth_agents.authentication_agent import (
    create_auth_status_agent,
    create_authenticated_session_with_agents,
)
from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentOutput,
)
from app.core.agents.action_prototype.utils import (
    detect_tool_call_loop_processor,
    limit_browser_tool_call_history_processor,
    trim_page_snapshots_processor,
)
from app.core.agents.utils.browser_utils.file_processing import (
    process_downloaded_files_v2,
)
from app.core.agents.utils.browser_utils.mcp_process_management import (
    stop_mcp_server_process,
)
from app.core.agents.utils.browser_utils.screenshot_upload import (
    S3ScreenshotUploadResult,
    upload_screenshot_from_bytes,
)
from app.core.agents.utils.storage_utils import generate_storage_state_path
from app.core.agents.utils.tool_call_log import tool_call_log_safe
from app.core.graph.deps.action_deps import ActionDeps, ToolActionDeps
from app.core.llm.model_registry import ModelRegistry
from config import PLAYWRIGHT_MCP_DIRECT

PLAYWRIGHT_BROWSER_AGENT_SYSTEM_PROMPT = """
You are a web automation assistant using Playwright tools, which has a Auto-wait feature. You should check the tool response carefully after each action to decide the next step. You need to complete the assigned task at your best.

## Starting Context
The browser session is authenticated for: {start_url}
Unless the task specifies a different URL, you should start your work at this URL.

## File Download Protocol
When downloading files:
1. Normally, you should click a link or button that triggers the download
2. Track all downloaded file paths in the "files" array, shown in tool response
3. Download only files directly relevant to the current task

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
- Pages may update asynchronously after interactions like clicks or navigation
- After such interactions, you may need to wait or refresh the page snapshot to see updated content

"""


async def process_tool_call(
    ctx: RunContext[ActionDeps],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    logs = []
    if len(tool_args) > 0:
        # only log the tool call if there are arguments in order to prettify the log
        logs.append(
            PlainTextLog(data=f"Processing tool call: {name} with args: {tool_args}")
        )

    target_tool_call = {"browser_click", "browser_type", "browser_navigate"}
    if name in target_tool_call:  # reduce the screenshot frequency
        res = await call_tool("browser_take_screenshot", {})
        if res:
            binary_data: BinaryContent = res[1]
            upload_result = upload_screenshot_from_bytes(binary_data.data, {})
            if isinstance(upload_result, S3ScreenshotUploadResult):
                logs.append(
                    S3ScreenshotLog(
                        key=upload_result.key, bucket=upload_result.bucket_name
                    )
                )
            else:
                logs.append(PlainTextLog(data=f"Screenshot: {upload_result.file_path}"))
    if logs:
        await tool_call_log_safe(ctx.deps.action_id, logs)
    return await call_tool(name, tool_args)


async def is_session_authenticated(storage_state_path: Path, test_url: str) -> bool:
    """Check if the stored session is still valid using authentication agent"""
    if not storage_state_path.exists():
        return False

    try:
        # Use the authentication agent to check status
        auth_result = await create_auth_status_agent(
            test_url=test_url,
            storage_state_path=storage_state_path,
            headless=True,
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
    by_pass_login: bool = False,
):
    """Create authenticated session using dynamic element detection agents"""
    logfire.info("Creating authenticated session with dynamic element detection...")
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
        by_pass_login=by_pass_login,
    )

    if auth_result.is_authenticated != "yes":
        raise ValueError(
            f"Failed to create authenticated session using agents: {auth_result.feedback}"
        )

    logfire.info(f"Authentication state saved to {storage_state_path}")
    return str(storage_state_path)


class ServerMode(str, Enum):
    EXTERNAL = "external"
    DIRECT = "direct"


class TaskDifficulty(str, Enum):
    SIMPLE = "simple"
    HARD = "hard"


DIFFICULTY_MODEL_MAP: dict[
    TaskDifficulty, dict[str, Literal["openai", "gemini"] | str]
] = {
    TaskDifficulty.SIMPLE: {
        "provider": "gemini",
        "model_name": "gemini-2.5-flash",
    },
    TaskDifficulty.HARD: {
        "provider": "gemini",
        "model_name": "gemini-2.5-flash",
    },
}

TOOLS2SKIP = {
    "browser_evaluate",
    "browser_network_requests",
    "browser_console_messages",
}


async def generic_browser_agent_playwright(
    ctx: RunContext[ToolActionDeps],
    task: str,
    homepage_url: str,
    username: str,
    password: str,
    storage_state_path: str,
    server_mode: ServerMode,
    # difficulty: TaskDifficulty = TaskDifficulty.HARD,
    mcp_server_url: str = "http://localhost:8931/mcp",
    external_downloads_path: Optional[str] = "playwright/files",
    skip_login: bool = False,
) -> GenericBrowserAgentOutput:
    """
    Playwright implementation that supports both external MCP server and direct MCP server modes.
    Args:
        server_mode: EXTERNAL uses MCPServerStreamableHTTP (for development only), DIRECT uses MCPServerStdio
        mcp_server_url: URL for external MCP server (only used in EXTERNAL mode)
        external_downloads_path: Path where external MCP server downloads files (only used in EXTERNAL mode, should match --output-dir)
        skip_login: Skip the authentication process for sites that don't require login
    """
    # difficulty: Task complexity level (SIMPLE or HARD). Defaults to HARD for better reliability.
    mode_name = (
        "External MCP Server"
        if server_mode == ServerMode.EXTERNAL
        else "Direct MCP Server"
    )
    logfire.info(f"Starting Generic Browser Agent (Playwright with {mode_name})")
    logfire.info(f"Task: {task}")
    deps = ctx.deps

    # Use external downloads path for EXTERNAL mode, default to browser deps path
    if server_mode == ServerMode.EXTERNAL:
        assert (
            external_downloads_path
        ), "external_downloads_path is required when using EXTERNAL server mode"
        downloads_path = external_downloads_path
    else:
        downloads_path = ctx.deps.action_working_dir

    # Authentication and storage state
    storage_state_path_obj = Path(storage_state_path)
    storage_state_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Check if authentication is valid (skip check if skip_login is True)
    if skip_login or not await is_session_authenticated(
        storage_state_path_obj, homepage_url
    ):
        if skip_login:
            logfire.info("Creating session without authentication")
        else:
            logfire.info(
                "No valid authentication found. Creating authenticated session..."
            )

        try:
            await create_authenticated_session(
                storage_state_path=storage_state_path_obj,
                username=username,
                password=password,
                login_url=homepage_url,  # Let the target URL redirect to login
                test_url=homepage_url,  # Use target URL for testing authentication
                by_pass_login=skip_login,
            )
            logfire.info("Session created successfully")
        except Exception as e:
            logfire.error(f"Failed to create session: {e}")
            raise
    else:
        logfire.info(f"Using existing valid authentication from {storage_state_path}")

    try:
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
                    str(storage_state_path_obj),
                    "--isolated",
                    "--no-sandbox",
                    "--headless",
                    "--output-dir",
                    str(downloads_path),
                    "--viewport-size",
                    "1280,900",
                ],
                timeout=30,
                max_retries=5,
                process_tool_call=process_tool_call,
            )

        # Map difficulty to model
        # model_config = DIFFICULTY_MODEL_MAP[difficulty]
        # provider: Literal["openai", "gemini"] = model_config["provider"]  # type: ignore
        # model_name: str = model_config["model_name"]  # type: ignore
        # logfire.info(
        #     f"Using model '{model_name}' from provider '{provider}' for task difficulty: {difficulty}"
        # )

        # Filter out browser_evaluate tool from the MCP server
        filtered_server = server.filtered(
            lambda ctx, tool_def: tool_def.name not in TOOLS2SKIP
        )

        # Create Pydantic AI agent with Playwright MCP integration
        agent = Agent(
            model=ModelRegistry.get_pydantic_ai_llm(ctx.deps.selected_model),
            toolsets=[filtered_server],
            output_type=GenericBrowserAgentOutput,
            history_processors=[
                detect_tool_call_loop_processor,
                limit_browser_tool_call_history_processor,
                trim_page_snapshots_processor,
            ],
            system_prompt=PLAYWRIGHT_BROWSER_AGENT_SYSTEM_PROMPT.format(
                start_url=homepage_url
            ),
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
                    usage_limits=UsageLimits(request_limit=70),
                    deps=ctx.deps,
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

    if parsed_result.successful == "no":
        raise ValueError(
            f"Generic browser agent failed to finish the task: {parsed_result.feedback}"
        )

    # Post-process files if any were downloaded
    if parsed_result.files:
        assert (
            ctx.deps.working_dir is not None
        ), "ctx.deps.working_dir is None, cannot process files"

        logfire.info(
            f"Processing downloaded files: {parsed_result.files} in working dir: {ctx.deps.action_working_dir}"
        )
        parsed_result.files = process_downloaded_files_v2(
            parsed_result.files,
            working_dir=ctx.deps.action_working_dir,
            raise_on_missing=True,
        )

    logfire.info(
        f"Generic browser agent ({mode_name}) execution result: {parsed_result}"
    )
    await ctx.deps.add_log(
        [
            PlainTextLog(data=f"Generic browser agent execute completed"),
            ObjectLog(data=parsed_result.model_dump()),
        ]
    )

    return parsed_result


def _run_external_mcp(
    action_working_dir: str, storage_state_path: str
) -> Optional[int]:

    # Check if port is already in use
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return False
            except OSError:
                return True

    port = 8931
    if is_port_in_use(port):
        logfire.info(
            f"Port {port} is already in use, reusing existing MCP server. Skipping server startup."
        )
        return None  # Return None to indicate we're reusing an existing server

    command = [
        "npx",
        "@playwright/mcp@0.0.40",
        "--storage-state",
        storage_state_path,
        "--isolated",
        "--output-dir",
        action_working_dir,
        "--viewport-size",
        "1280,900",
        "--port",
        str(port),
    ]

    logfire.info(f"Starting service: {' '.join(command)}")

    try:

        process = subprocess.Popen(
            command,
            stdout=None,  # Show output in the terminal, or set to subprocess.PIPE to capture
            stderr=None,  # Show errors in the terminal, or set to subprocess.PIPE to capture
        )

        logfire.warning(
            f"Service started successfully, process ID (PID): {process.pid}"
        )

        time.sleep(3)

        if process.poll() is None:
            logfire.info("Service is running in the background.")
            return process.pid
        else:
            raise Exception(
                f"Service has exited in the background, return code: {process.returncode}"
            )
    except Exception as e:
        logfire.error(f"An error occurred: {e}")
        raise


async def browser_tool(
    ctx: RunContext[ToolActionDeps],
    task: str,
    homepage_url: str,
    crendential_key_name: Optional[str] = None,
    # difficulty: TaskDifficulty = TaskDifficulty.HARD,
) -> GenericBrowserAgentOutput:
    """
    Execute browser automation tasks with automatic model selection based on task difficulty.

    Args:
        ctx: Runtime context containing dependencies like credentials and working directory
        task: Natural language description of the browser automation task to perform
        homepage_url: The starting URL for the browser session (used for authentication and initial navigation)
        crendential_key_name: Optional key name for login credentials, if authentication is required

    Returns:
        GenericBrowserAgentOutput containing task results
    """
    if crendential_key_name:
        if crendential_key_name not in ctx.deps.credentials:
            raise ModelRetry(
                f"credential name '{crendential_key_name}' not found in credentials. Keys are: {ctx.deps.credentials.keys()}"
            )
        credential = ctx.deps.credentials[crendential_key_name]
        if isinstance(credential, LoginCredentialModel):
            username = credential.user_name
            password = credential.password
        else:
            raise ModelRetry(
                f"credential '{crendential_key_name}' is not a login credential"
            )
        skip_login = False
    else:
        username = ""
        password = ""
        skip_login = True  # No credentials provided, skip login
    #   difficulty: Task complexity level (SIMPLE or HARD). Defaults to HARD for better reliability.
    logfire.info(f"Selected model: {ctx.deps.selected_model}")
    try:
        current_directory = ctx.deps.action_working_dir

        if not skip_login:
            # Ensure username and password are provided when authentication is required
            if not username or not password:
                raise ValueError(
                    "username and password are required when skip_login=False"
                )
            storage_state_path = generate_storage_state_path(
                homepage_url, username, password
            )
        else:
            # Use a simple storage state path for non-authenticated sessions
            storage_state_path = str(
                Path(ctx.deps.action_working_dir) / "anonymous_session.json"
            )
            logfire.info("Skipping authentication - running in anonymous mode")

        if PLAYWRIGHT_MCP_DIRECT:
            server_mode = ServerMode.DIRECT
        else:
            server_mode = ServerMode.EXTERNAL
            mcp_server_pid = _run_external_mcp(
                ctx.deps.action_working_dir, storage_state_path
            )
            ctx.deps.mcp_server_pid = mcp_server_pid

        prompt = f"Always start by going to homepage {homepage_url} and then perform the task \n{task}"
        logfire.warning(f"Server Mode: {server_mode}")
        result = await generic_browser_agent_playwright(
            username=username or "",
            password=password or "",
            storage_state_path=storage_state_path,
            ctx=ctx,
            task=prompt,
            homepage_url=homepage_url,
            # difficulty=difficulty,
            server_mode=server_mode,
            external_downloads_path=f"{current_directory}",
            skip_login=skip_login,
        )

        return result
    except Exception as e:
        logfire.error(f"Error in generic_browser_agent_playwright_direct: {e}")
        raise ModelRetry(f"Browser agent error (retryable): {str(e)}")
    finally:
        if hasattr(ctx.deps, "mcp_server_pid") and ctx.deps.mcp_server_pid:
            logfire.info("cleaning up external MCP server process")
            stop_mcp_server_process(ctx.deps.mcp_server_pid)
