from pathlib import Path
from typing import List, Optional

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from browser_use import ActionResult
from browser_use import Agent as BrowserUseAgent
from browser_use import Controller
from pydantic_ai import RunContext, Tool

from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentOutput,
)
from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.browser_use_llm.openai_model import get_browser_use_openai_llm


async def generic_browser_agent(
    ctx: RunContext[ActionDeps],
    task: str,
    max_steps: int = 20,
    model_name: str = "gpt-4.1",
    use_vision: bool = False,
    excluded_actions: Optional[List[str]] = None,
) -> GenericBrowserAgentOutput:
    """
    A generic browser agent that can execute any browser-based task.

    Args:
        task: The specific task instructions for the browser agent to execute
        max_steps: Maximum number of steps the agent can take (default: 20)
        model_name: The LLM model to use (default: "gpt-4.1")
        use_vision: Whether to enable vision capabilities (default: False)
        excluded_actions: List of actions to exclude from the agent
    """

    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)
        await ctx.deps.add_log(model_output_logs + screenshot_logs)

    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()

    llm = get_browser_use_openai_llm(model_name=model_name)

    # Set default excluded actions if none provided
    if excluded_actions is None:
        excluded_actions = ["search_google", "open_tab"]

    controller = Controller(
        exclude_actions=excluded_actions,
        output_model=GenericBrowserAgentOutput,
    )

    @controller.action("Verify downloaded files")
    async def verify_downloaded_files(self):
        assert ctx.deps.working_dir is not None
        download_dir = Path(ctx.deps.working_dir) / "downloads"
        result = []
        if download_dir.exists():
            for file in download_dir.iterdir():
                if file.is_file():
                    result.append(file.name)
        logfire.info(f"Generic Browser Agent > Downloaded files: {result}")
        return ActionResult(extracted_content=f"Downloaded files: {result}")

    logfire.info("Starting Generic Browser Agent")
    logfire.info(f"Task: {task}")

    assert browser_deps is not None
    agent = BrowserUseAgent(
        task=task,
        browser_session=browser_deps.browser_session,
        llm=llm,
        controller=controller,
        use_vision=use_vision,
        file_system_path=str(browser_deps.execution_space_path / "file_system"),
        calculate_cost=True,
    )

    agent_result = await agent.run(
        max_steps=max_steps,
        on_step_end=hook_on_step_end,
    )

    raw_result = agent_result.final_result()
    if not raw_result:
        raise ValueError("No result from the agent")

    try:
        parsed_result = GenericBrowserAgentOutput.model_validate_json(raw_result)
        logfire.info(f"Generic browser agent execution result: {parsed_result}")
    except (ValueError, TypeError) as parse_error:
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Failed to parse agent response as JSON"),
                PlainTextLog(data=raw_result),
            ]
        )
        raise ValueError(
            f"Failed to parse agent response as JSON: {parse_error}"
        ) from parse_error

    await ctx.deps.add_log(ObjectLog(data=parsed_result.model_dump()))

    if parsed_result.successful == "no":
        raise ValueError(
            f"Generic browser agent failed to finish the task: {parsed_result.feedback}"
        )

    # Post-process files if any were downloaded
    if parsed_result.files:
        files_with_path = []
        assert (
            ctx.deps.working_dir
        ), "ctx.deps.working_dir is None, cannot save post-process files"
        download_dir = Path(ctx.deps.working_dir) / "downloads"
        logfire.info(f"Checking Dir: {download_dir}")

        for file in parsed_result.files:
            file_path = download_dir / file
            if file_path.exists():
                files_with_path.append(str(file_path))
            else:
                logfire.warning(f"File {file} not found in the downloads folder")

        parsed_result.files = files_with_path

    return parsed_result


generic_browser_agent_tool = Tool(generic_browser_agent, takes_ctx=True)
