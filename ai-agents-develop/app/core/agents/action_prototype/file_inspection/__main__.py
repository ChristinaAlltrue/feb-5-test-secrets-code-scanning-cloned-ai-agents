import asyncio

import logfire
from pydantic_ai import Agent, Tool

from app.core.agents.action_prototype.file_inspection.schema import FileInspectionOutput
from app.core.agents.action_prototype.file_inspection.tools import file_process
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.base_deps import ControlInfo
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


async def main():
    # demo of the usage. use your own files.
    files = [
        "./local_tmp_files/test.txt",
        "./local_tmp_files/test2.csv",
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
        output_type=FileInspectionOutput,
        deps_type=ActionDeps,
        tools=[Tool(file_process, takes_ctx=True)],
    )

    result = await agent.run(
        f"Can you tell me do they contain some similar information in these two files: {files}",
        deps=deps,
    )
    await deps.dispose()
    return result


if __name__ == "__main__":
    logfire.configure()
    res = asyncio.run(main())
    print(res)
