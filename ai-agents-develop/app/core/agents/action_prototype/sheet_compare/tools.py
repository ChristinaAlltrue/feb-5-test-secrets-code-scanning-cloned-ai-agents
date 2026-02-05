import logfire
from pydantic_ai import RunContext

from app.core.agents.utils.openai_utils.response_with_tool_code_interpreter import (
    run_code_with_container,
)
from app.core.graph.deps.base_deps import BaseDeps

# TODO: Eventhough the code interpreter can not support structured output, we can try to add a structured format instruction and ask LLM to generate the downloadable json file

instruction_template = """
Your goal is:
- Compare these two files by writing and executing python code.
- Generate three downloadable csv files with the following definitions:
  1. 'added.csv' for new users,
  2. 'removed.csv' for users no longer in the list,
  3. 'changed.csv' for users whose details have changed.

When you generate the changed.csv, you have to choose the column that should be the primary key and the column that should be the update identifier to define what is changed.

You must explain your approach used to compare the sheets and the thinking behind it, like:
    - which file is the base file you chose as the base file
    - which column was chosen as the primary key
    - which column was chosen as the update identifier


if the user_instruction has any conflict with the above instructions, please follow the user_instruction.

user_instructions:
{instructions}
"""


async def compare_sheets(
    ctx: RunContext[BaseDeps], file_path_list: list[str], instructions: str
):
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
    if len(file_path_list) != 2:
        raise ValueError(
            f"Expected exactly 2 files for comparison, got {len(file_path_list)}"
        )

    output = await run_code_with_container(
        ctx.deps.working_dir,
        file_path_list,
        instruction_template.format(instructions=instructions),
        container_name="sheet-compare",  # TODO: use different container for each control execution, currently, we reuse the same container to save money.
    )

    return output
