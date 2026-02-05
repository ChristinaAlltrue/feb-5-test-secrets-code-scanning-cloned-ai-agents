from pathlib import Path
from typing import Any, List
from uuid import uuid4

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from browser_use import ActionResult
from browser_use import Agent as BrowserUseAgent
from browser_use import Browser, Tools
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, Tool

from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.browser_use_llm import get_browser_use_llm


class ScreenshotEvidence(BaseModel):
    page_url: str = Field(
        description="The URL of the page",
    )
    screenshot_path: str = Field(
        description="The path of the screenshot",
    )
    screenshot_info: str = Field(
        description="The information in the screenshot",
        default="",
    )


class ScreenshotEvidenceList(BaseModel):
    evidences: List[ScreenshotEvidence] = Field(
        description="The url of the page, the screenshots path and the information of the task",
    )


async def github_evidence_screenshot(
    ctx: RunContext[ActionDeps],
    pr_url: str,
    navigation_instructions: str,
    screenshot_target: str,
) -> ScreenshotEvidenceList:
    """
    Take screenshots as evidence for the github PR
    The browser will navigate to the PR URL, and take a screenshot of the given target.

    Args:
        pr_url: The URL of the PR.
        navigation_instructions: The instructions for navigation to the page andthe screenshot.
        screenshot_target: The target of the screenshot.
    """

    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)

        await ctx.deps.add_log(model_output_logs + screenshot_logs)

    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()

    llm = get_browser_use_llm(provider="gemini", model_name="gemini-2.5-flash")
    initial_actions = []
    initial_actions.append({"navigate": {"url": pr_url, "new_tab": False}})

    tools = Tools[Any](
        exclude_actions=["search", "switch", "screenshot"],
        output_model=ScreenshotEvidenceList,
    )

    @tools.action(description="Take a screenshot of the target page")
    async def take_screenshot(browser_session: Browser):
        page = await browser_session.must_get_current_page()
        url = await page.get_url()
        screenshot_path = (
            Path(ctx.deps.action_working_dir) / f"screenshot_{uuid4()}.png"
        )
        await browser_session.take_screenshot(path=screenshot_path, full_page=False)
        logfire.info(f"Screenshot saved to {screenshot_path}")

        return ActionResult(
            extracted_content=f"Take screenshot successfully. The screenshot path is: {str(screenshot_path)}. The url of the page is: {url}",
            include_in_memory=True,
        )

    @tools.action(description="take a full page screenshot of the target page")
    async def take_full_page_screenshot(browser_session: Browser):
        page = await browser_session.must_get_current_page()
        url = await page.get_url()
        screenshot_path = (
            Path(ctx.deps.action_working_dir) / f"full_page_screenshot_{uuid4()}.png"
        )
        await browser_session.take_screenshot(path=screenshot_path, full_page=True)
        logfire.info(f"Full page screenshot saved to {screenshot_path}")
        return ActionResult(
            extracted_content=f"Take full page screenshot successfully. The screenshot path is: {str(screenshot_path)}. The url of the page is: {url}",
            include_in_memory=True,
        )

    agent = BrowserUseAgent(
        initial_actions=initial_actions,
        task="""
        Navigate to the target page, and take a screenshot of the given target.
        * You must call `take_screenshot` when you navigate and saw the target info. Once you got the screenshot, it means you have completed the task.
        * Before you call `take_screenshot`, you have to summarize the information of the page as the `screenshot_info`.
        * You must call `take_full_page_screenshot` once and only once when you navigate to the target page.
        * Before you finished the task, make sure you have called `take_full_page_screenshot` at least once.
        Navigation instructions: {navigation_instructions}
        target: {screenshot_target}
        """.format(
            navigation_instructions=navigation_instructions,
            screenshot_target=screenshot_target,
        ),
        browser_session=browser_deps.browser_session,
        llm=llm,
        tools=tools,
        use_vision=True,
        file_system_path=browser_deps.execution_space_path / "file_system",
    )
    agent_result = await agent.run(
        max_steps=10,
        on_step_end=hook_on_step_end,
    )

    raw_result = agent_result.final_result()
    if not raw_result:
        raise ValueError("No result from the agent")

    try:
        parsed_result = ScreenshotEvidenceList.model_validate_json(raw_result)
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

    await ctx.deps.add_log(
        [
            PlainTextLog(data="Successfully parsed agent response"),
            ObjectLog(data=parsed_result.model_dump()),
        ]
    )

    logfire.info(f"Screenshot evidence: {parsed_result}")

    return parsed_result


github_evidence_screenshot_tool = Tool(github_evidence_screenshot, takes_ctx=True)
