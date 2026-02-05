import logfire
from pydantic_ai import RunContext

from app.core.agents.utils.openai_utils.response_with_tool_code_interpreter import (
    run_code_with_container,
)
from app.core.graph.deps.base_deps import BaseDeps

# TODO: Eventhough the code interpreter can not support structured output, we can try to add a structured format instruction and ask LLM to generate the downloadable json file

instruction_template = """
I need you to do the following tasks for the files provided:
{instructions}
"""


async def file_process(
    ctx: RunContext[BaseDeps], file_path_list: list[str], instructions: str
) -> str:
    """
    Compare two sheets and return the differences

    Args:
        file_path_list: The list of file paths to compare, example: ["/Users/john/Downloads/sheet1.xlsx", "/Users/john/Downloads/sheet2.xlsx"]
        instructions: The instructions for the comparison

    """
    logfire.info(
        f"Working dir: {ctx.deps.working_dir}, File path list: {file_path_list}, Instructions: {instructions}"
    )
    # only support two files comparison
    output = await run_code_with_container(
        ctx.deps.working_dir,
        file_path_list,
        instruction_template.format(instructions=instructions),
        container_name="file-inspection",  # TODO: use different container for each control execution, currently, we reuse the same container to save money.
    )

    return output
