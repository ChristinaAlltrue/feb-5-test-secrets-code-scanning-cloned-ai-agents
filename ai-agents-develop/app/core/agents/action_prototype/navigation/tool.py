from typing import Literal

import logfire
from browser_use import Agent as BrowserUseAgent
from browser_use import Controller
from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from app.core.agents.action_prototype.navigation.schema import NavigationOutput
from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.base_deps import BaseDeps
from app.core.llm.browser_use_llm.openai_model import get_browser_use_openai_llm


class GeneralResponse(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description=f"yes or no, whether the navigation was successful"
    )
    feedback: str


async def navigation(
    ctx: RunContext[BaseDeps],
    instructions: str,
    goal: str,
    initial_url: str,
    max_steps: int = 8,
):
    """
    Navigate on the browser.

    Args:
        ctx: The context of the action execution.
        instructions: The instructions to navigate on the browser.
        goal: The goal of the navigation.
        initial_url: The initial URL to navigate to.
        max_steps: The maximum number of steps to take.
    """

    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)

        await ctx.deps.add_log(model_output_logs + screenshot_logs)

    logfire.info("Running navigation action")
    try:
        nav_to_proj_prompt = """
            Doing the following steps one by one, take ONLY one action at a time.
            If there is anything you take that you have to login, stop and successful is `no`.
            instructions:
            {}
            Final Step: {}. Then stop here.
        """.format(
            instructions, goal
        )

        browser_deps = ctx.deps.get_browser_deps()
        if not browser_deps:
            ctx.deps.init_browser_deps()
            browser_deps = ctx.deps.get_browser_deps()

        browser_session = browser_deps.browser_session

        initial_actions = []
        if initial_url:
            initial_actions.append({"navigate": {"url": initial_url, "new_tab": False}})

        llm = get_browser_use_openai_llm()

        controller = Controller(
            exclude_actions=["search_google", "open_tab"],
            output_model=GeneralResponse,
        )
        agent = BrowserUseAgent(
            initial_actions=initial_actions,
            task=nav_to_proj_prompt,
            browser_session=browser_deps.browser_session,
            llm=llm,
            controller=controller,
            use_vision=True,
            file_system_path=browser_deps.execution_space_path / "file_system",
        )
        agent_result = await agent.run(
            max_steps=max_steps,
            on_step_end=hook_on_step_end,
        )

        raw_result = agent_result.final_result()
        if raw_result:
            parsed_result: GeneralResponse = GeneralResponse.model_validate_json(
                raw_result
            )
        else:
            raise ValueError("Agent exited without returning a response")

        current_page = await browser_session.get_current_page()

        result = NavigationOutput(
            successful=parsed_result.successful,
            current_url=current_page.url,
            feedback=parsed_result.feedback,
        )
        result = result.model_dump()
        logfire.info(f"Navigation result: {result}")

        return result

    except Exception as e:
        logfire.error(f"Error in Navigation: {e}")
        raise
