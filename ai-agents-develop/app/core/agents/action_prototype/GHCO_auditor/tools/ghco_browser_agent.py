from pathlib import Path
from typing import List, Literal

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from browser_use import ActionResult
from browser_use import Agent as BrowserUseAgent
from browser_use import Controller
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, Tool

from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.browser_use_llm.openai_model import get_browser_use_openai_llm


class GHCOBrowserAgentOutput(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description="Whether the browser agent finished the task",
    )
    feedback: str = Field(
        description="The feedback from the browser agent",
    )
    execution_flow: str = Field(
        description="The execution flow of the browser agent",
    )
    files: List[str] = Field(
        description="The original file names that are downloaded",
    )


async def ghco_browser_agent(
    ctx: RunContext[ActionDeps],
    navigation_instruction: str,
    target_business_unit: List[str],
) -> GHCOBrowserAgentOutput:
    """
    This tool is used to navigate to the GHCO website and download the files related to the targets.
    The tool will navigate to the GHCO website, and download the files related to the targets.
    The tool will return the list of the files that are downloaded.

    Args:
        business_units: The list of the business units that the user wants the agent to check.
        navigation_instruction: The instructions for navigation to the page and download the files.
    """

    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)

        await ctx.deps.add_log(model_output_logs + screenshot_logs)

    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()

    llm = get_browser_use_openai_llm(model_name="gpt-4.1-mini")

    controller = Controller(
        exclude_actions=["search_google", "open_tab"],
        output_model=GHCOBrowserAgentOutput,
    )

    @controller.action("Verify the files have been downloaded")
    async def verify_downloaded_files(self):
        download_dir = Path(ctx.deps.working_dir) / "downloads"
        result = []
        for file in download_dir.iterdir():
            if file.is_file():
                file_name = file.name
                result.append(file_name)
        logfire.info(f"Browser Agent > Downloaded files: {result}")
        return ActionResult(extracted_content=f"Downloaded files: {result}")

    agent = BrowserUseAgent(
        task="""
        Doing the following steps one by one, take ONLY one action at a time.
        {navigation_instruction}

        target business units: {target_business_unit}

        Make sure you have downloaded all the files you need to download. Do not download non-relevant files.

        Notice:
            - The file list is a table; scroll the table itself to search for the files you need.
            - Business unit info is in the `Request Description` column. For example, you will see 'Test User List 2 - ARCS'. If your target business unit includes 'ARCS', download that file.
            - For one business unit, there are typically two rows in the table; download both files if present.
            - Download each file only once.
            - Before ending the task, call verify_downloaded_files to confirm the target files were downloaded. If any are missing, continue downloading. Include the original file names in the output; do not modify them.
        """.format(
            target_business_unit=target_business_unit,
            navigation_instruction=navigation_instruction,
        ),
        browser_session=browser_deps.browser_session,
        llm=llm,
        controller=controller,
        use_vision=True,
        file_system_path=browser_deps.execution_space_path / "file_system",
    )
    agent_result = await agent.run(
        max_steps=20,
        on_step_end=hook_on_step_end,
    )

    raw_result = agent_result.final_result()
    if not raw_result:
        raise ValueError("No result from the agent")

    try:
        parsed_result = GHCOBrowserAgentOutput.model_validate_json(raw_result)
        logfire.info(f"Browser agent execution result: {parsed_result}")
    except (ValueError, TypeError) as parse_error:
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Failed to parse agent response as JSON"),
                ObjectLog(data=raw_result),
            ]
        )
        raise ValueError(
            f"Failed to parse agent response as JSON: {parse_error}"
        ) from parse_error

    # add the execution log
    await ctx.deps.add_log(ObjectLog(data=parsed_result.model_dump()))

    if parsed_result.successful == "no":
        raise ValueError(
            f"Browser agent failed to finish the task: {parsed_result.feedback}"
        )

    # post process the result
    files_with_path = []
    logfire.info(f"Checking Dir: {Path(ctx.deps.working_dir) / 'downloads'}")
    for file in parsed_result.files:
        file_path = Path(ctx.deps.working_dir) / "downloads" / file
        if file_path.exists():
            files_with_path.append(str(file_path))
        else:
            raise ValueError(f"File {file} not found in the downloads folder")

    parsed_result.files = files_with_path

    return parsed_result


ghco_browser_agent_tool = Tool(ghco_browser_agent, takes_ctx=True)
