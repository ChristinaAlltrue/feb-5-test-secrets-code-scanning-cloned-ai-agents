import asyncio

from pydantic_ai import Agent, Tool

from app.core.agents.action_prototype.login.schema import LoginOutput
from app.core.agents.action_prototype.login.tool import login
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
        output_type=LoginOutput,
        deps_type=ActionDeps,
        tools=[Tool(login, takes_ctx=True)],
    )
    res = await agent.run(
        """
        Login to http://localhost:8087 with the following credentials:
        Username: roger
        Password: 1234
        the MFA secret is "AV2VOBOABAALBS6ZGMLLXJNE34HWER6K"
        when You see the DEMO page, means the login is successful.
        """,
        deps=deps,
    )
    await deps.dispose()
    return res


if __name__ == "__main__":
    import logfire

    logfire.configure()
    res = asyncio.run(main())
    print(res)
