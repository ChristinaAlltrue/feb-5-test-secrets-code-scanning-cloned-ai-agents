import asyncio

from pydantic_ai import Agent, Tool

from app.core.agents.action_prototype.navigation.schema import NavigationOutput
from app.core.agents.action_prototype.navigation.tool import navigation
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
        output_type=NavigationOutput,
        deps_type=ActionDeps,
        tools=[Tool(navigation, takes_ctx=True)],
    )
    res = await agent.run(
        """
        Navigate to the https://en.wikipedia.org/wiki/Main_Page.
        serch the tariff and get the first paragraph.
        Final Step: get the first paragraph of the search result.
        """,
        deps=deps,
    )
    await deps.dispose()
    return res


if __name__ == "__main__":
    res = asyncio.run(main())
    print(res)
