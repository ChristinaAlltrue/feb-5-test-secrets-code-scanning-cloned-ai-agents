import asyncio

import logfire
from pydantic_ai import Agent, Tool

from app.core.agents.action_prototype.sheet_compare.schema import SheetCompareOutput
from app.core.agents.action_prototype.sheet_compare.tools import compare_sheets
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.base_deps import ControlInfo
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


async def main():
    # demo of the usage. use your own files.
    files = [
        "./local_tmp_files/Gamma-Users-071124.csv",
        "./local_tmp_files/Gamma-Users-110624.csv",
    ]
    logfire.info("Starting the script")

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
        output_type=SheetCompareOutput,
        deps_type=ActionDeps,
        tools=[Tool(compare_sheets, takes_ctx=True)],
    )

    result = await agent.run(
        f"Compare the two sheets: {files}",
        deps=deps,
    )
    await deps.dispose()
    return result


if __name__ == "__main__":
    logfire.configure()
    res = asyncio.run(main())
    print(res)
