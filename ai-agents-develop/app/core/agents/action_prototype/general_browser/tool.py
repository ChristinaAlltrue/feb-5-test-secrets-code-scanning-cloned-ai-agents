from typing import List, Literal, Optional

import logfire
from browser_use import ActionResult
from browser_use import Agent as BrowserUseAgent
from browser_use import Controller
from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from app.core.agents.action_prototype.general_browser.audit_tools.audit_detector import (
    audit_page,
)
from app.core.agents.action_prototype.general_browser.feedback_generator.feedback_generator import (
    get_real_feedback,
)
from app.core.agents.action_prototype.general_browser.schema import GeneralBrowserOutput
from app.core.agents.action_prototype.general_browser.screenshot_detector.screenshot_detector import (
    filter_relevant_screenshots,
)
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.browser_info import (
    BrowserInfo,
)
from app.core.agents.action_prototype.screenshot.image_process.image_spliter import (
    save_blocks_as_images,
)
from app.core.agents.action_prototype.screenshot.image_process.screenshot_process import (
    take_screenshot,
)
from app.core.agents.action_prototype.screenshot.tools import screenshot_action
from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.base_deps import BaseDeps
from app.core.llm.browser_use_llm.openai_model import get_browser_use_openai_llm


class GeneralBrowserException(Exception):
    """Custom exception raised for errors in general browser operations."""


class BrowserScreenshotException(Exception):
    """Custom exception raised for errors in processing screenshots."""


class BrowserInfoCheckException(Exception):
    """Custom exception raised for errors in browser information checking and auditing."""


class GeneralResponse(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description="yes or no, whether the general browser was successful"
    )
    feedback: str
    downloaded_files: List[str] = Field(
        default_factory=list,
        description="List of names of files downloaded during the general browser action",
        json_schema_extra={"example": ["file1.txt", "file2.pdf"]},
    )


async def general_browser(
    ctx: RunContext[BaseDeps],
    instructions: str,
    goal: str,
    initial_url: str,
    target_information: str = "",
    audit_instructions: str = "",
    max_steps: int = 30,
    generated_info: Optional[BrowserInfo] = None,
    retry_steps: int = 1,
) -> dict:
    """
    Navigate on the browser.

    Args:
        ctx: The context of the action execution.
        instructions: The instructions to navigate on the browser.
        goal: The goal of the general browser.
        initial_url: The initial URL to navigate to.
        target_information: Information to check and take screenshots of.
        audit_instructions: Instructions for auditing page content.
        max_steps: The maximum number of steps to take.
        generated_info: Optional BrowserInfo object to store metadata.
        retry_steps: Number of retry attempts if the agent fails.
    """

    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)

        await ctx.deps.add_log(model_output_logs + screenshot_logs)

    logfire.info("Running general_browser action")
    try:
        target_info_section = (
            f"""You also have a task about checking if some information is present and taking screenshots of them: If the instruction requires you to check and take screenshots of some information on some steps, when you are operating that step, check if the information you need is present by using the tool `screenshot_check` with the target information.
            The target information is:
            {{{target_information}}}
            Remember you *MUST* run the tool `screenshot_check` to check if the information is present if the instruction requires it.
            If the target_information said "take screenshot of something", then you *MUST* use the tool `screenshot_check` when you are operating that step.
            And you need to generate the input for the tool `screenshot_check` with the target information. The input should not include things like "take screenshot of" or "check if", just the information you need to check or take screenshot of.
            If the instructions require you to check if the information is in the page, you *MUST* use the tool `screenshot_check` to check if the information is present on the page.
            On each page, you may run the screenshot_check tool at most once, regardless of how many targets or steps require it, as long as the page has not changed (by navigation, reload, or update).
            It does not matter how many different targets or steps are requested—never run screenshot_check more than once for the same, unchanged page.
            Only run screenshot_check again after the page content has changed.
            """
            if target_information
            else ""
        )
        audit_section = (
            f"""Another task you need to do is to audit the page based on the instructions provided. If the instructions require you to audit, verify, or check some information on the page, you need to use the tool `audit_information` with the instructions.:
            {{{audit_instructions}}}
            Remember you *MUST* run the tool `audit_information` to audit the page if the instructions require it in certain steps.
            Do not run the `audit_information` tool more than once on the same page if the page has not changed since the last audit.
            """
            if audit_instructions
            else ""
        )
        tried_steps_navigation = 3
        nav_to_proj_prompt = """
            Doing the following steps one by one, take ONLY one action at a time.
            If there is anything you take that you have to login, stop and successful is `no`.
            You are only allowed to click buttons that the instructions said to click.
            You are only allowed to type the information that the instructions said to type.
            Do not click any buttons that the instructions did not say to click.
            Do not type any information that the instructions did not say to type.
            instructions:
            {{{instructions}}}
            Final Step: {goal}. Then stop here.
            {target_info_section}
            {audit_section}
            If you need to download any files, you need to add the name of the downloaded file to the `downloaded_files` field which is a list in the output.
            Every time you download a file, you *MUST* add the name of the file to the `downloaded_files` field.
            If you have been tried same steps for {tried_steps_navigation} times and still not achieved the goal, you should stop and return `successful` as `no` and `feedback` as "I have been tried same steps for {tried_steps_navigation} times and still not achieved the goal. I will stop here.".
            If you already achieved the last goal, you should stop and return `successful` as `yes` and `feedback` as "I have achieved the goal: {goal}. I will stop here.". DO NOT keep doing the same steps that have been done successfully.
        """.format(
            instructions=instructions,
            goal=goal,
            target_info_section=target_info_section,
            audit_section=audit_section,
            tried_steps_navigation=tried_steps_navigation,
        )
        browser_deps = ctx.deps.get_browser_deps()
        if not browser_deps:
            ctx.deps.init_browser_deps()
            browser_deps = ctx.deps.get_browser_deps()

        browser_context = browser_deps.browser_session.browser_context

        initial_actions = []
        if initial_url:
            initial_actions.append({"navigate": {"url": initial_url, "new_tab": False}})

        llm = get_browser_use_openai_llm()

        controller = Controller(
            exclude_actions=["search_google", "open_tab"],
            output_model=GeneralResponse,
        )

        @controller.action("Check if some of the information user want is on this page")
        async def screenshot_check(target_info: str):
            # If the target_info is found on the page.
            try:
                page = await browser_deps.browser_session.get_current_page()
                html = await page.content()
                screenshot = await take_screenshot(
                    browser_deps.browser_session, full_page=True
                )
                output = await filter_relevant_screenshots(
                    html, target_info, screenshot
                )
                if output == "yes":
                    screenshots = await screenshot_action(
                        browser_session=browser_deps.browser_session,
                        target_info=target_info,
                        full_page_screenshot=True,
                    )
                    working_dir = ctx.deps.working_dir
                    if generated_info:
                        # TODO: we don't have a way to save screenshot info and analyse it yet, so I put an empty list here
                        img_list = save_blocks_as_images(
                            screenshots,
                            working_dir,
                            str(len(generated_info.screenshot_info)),
                        )
                        generated_info.add_screenshot_info(
                            page.url, img_list, target_info
                        )
                return ActionResult(
                    extracted_content=f"Runned screenshot_check for target {target_info} on {page.url}"
                )
            except Exception as e:
                logfire.error(f"Error in screenshot_check: {e}")
                raise BrowserScreenshotException(
                    f"Failed to check screenshot: {e}"
                ) from e

        @controller.action("Check if the information on this page fit the requirements")
        async def audit_information(audit_instructions: str):
            # If the information on the page fit the requirements.
            try:
                page = await browser_deps.browser_session.get_current_page()
                html = await page.content()
                output = await audit_page(html, audit_instructions)
                if output.has_info == "yes":
                    if generated_info:
                        generated_info.add_check_info(
                            url=page.url,
                            pass_or_not=output.pass_audit,
                            reason=output.reason,
                        )
                return ActionResult(
                    extracted_content=f"Runned audit_information for instruction: {audit_instructions} on {page.url}"
                )
            except Exception as e:
                logfire.error(f"Error in audit_information: {e}")
                raise BrowserInfoCheckException(
                    f"Failed to audit information: {e}"
                ) from e

        agent_successful = "no"
        parsed_result = None
        while retry_steps >= 1 and agent_successful == "no":
            agent = BrowserUseAgent(
                initial_actions=initial_actions,
                task=nav_to_proj_prompt,
                browser_session=browser_deps.browser_session,
                llm=llm,
                controller=controller,
                use_vision=False,
                file_system_path=browser_deps.execution_space_path / "file_system",
            )
            agent_result = await agent.run(
                max_steps=max_steps,
                on_step_end=hook_on_step_end,
            )

            raw_result = agent_result.final_result()
            if raw_result:
                try:
                    parsed_result = GeneralResponse.model_validate_json(raw_result)
                except (ValueError, TypeError) as parse_error:
                    raise ValueError(
                        f"Failed to parse agent response as JSON: {parse_error}"
                    ) from parse_error
            else:
                raise ValueError("Agent exited without returning a response")
            agent_successful = parsed_result.successful
            retry_steps -= 1
        if parsed_result is None:
            raise ValueError("No agent execution completed successfully")

        current_page = await browser_deps.browser_session.get_current_page()
        final_feedback = parsed_result.feedback
        if parsed_result.successful == "no":
            screenshots = agent_result.screenshots()
            final_feedback = await get_real_feedback(
                original_feedback=parsed_result.feedback,
                screenshot=screenshots[-1] if screenshots else "",
                user_prompt=instructions,
            )

        result = GeneralBrowserOutput(
            successful=parsed_result.successful,
            current_url=current_page.url,
            feedback=final_feedback,
            downloaded_files=parsed_result.downloaded_files,
        )
        result = result.model_dump()
        logfire.info(f"GeneralBrowser result: {result}")

        return result

    except Exception as e:
        logfire.error(f"Error in GeneralBrowser: {e}")
        raise GeneralBrowserException(f"GeneralBrowser action failed: {e}") from e
