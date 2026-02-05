import asyncio

from pydantic_ai import Agent, Tool

from app.core.agents.action_prototype.general_browser.schema import GeneralBrowserOutput
from app.core.agents.action_prototype.general_browser.tool import general_browser
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.base_deps import ControlInfo
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


async def main():
    control_info = ControlInfo(
        control_id="00000000-0000-0000-0000-000000000000",
        control_execution_id="00000000-0000-0000-0000-000000000000",
        entity_id="00000000-0000-0000-0000-000000000000",
    )
    deps = ActionDeps(
        action_id="00000000-0000-0000-0000-000000000000",
        control_info=control_info,
        write_db_log=False,
    )
    agent = Agent(
        model=get_pydanticai_openai_llm(),
        output_type=GeneralBrowserOutput,
        deps_type=ActionDeps,
        tools=[Tool(general_browser, takes_ctx=True)],
    )
    res = await agent.run(
        """
        Navigate to the https://github.com/microsoft/fluentui-system-icons/pulls.
        Click the first two pull requests on the page by order (You might need to go back to the first page after you click one).
        Check if there is any information about Base Repository.
        Final Step: go back to the original page. And return the URLs of the pull requests that contain information about Base Repository.
        """,
        deps=deps,
    )
    await deps.dispose()
    return res


if __name__ == "__main__":
    res = asyncio.run(main())
    print(res)
