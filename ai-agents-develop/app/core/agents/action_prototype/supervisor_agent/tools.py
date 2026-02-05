import re
from pathlib import Path
from typing import List

import logfire
from pydantic_ai import RunContext, Tool

from app.core.graph.deps.action_deps import ActionDeps


def get_file_list_in_control_execution_dir(ctrl_exec_dir: str) -> List[Path]:
    """
    Get the list of files in the control execution directory.
    filter out the auto-generated files like graph_state.json and page-*.png
    """
    base_path = Path(ctrl_exec_dir)
    result: List[Path] = []

    ignore_patterns = [
        re.compile(r"^page-.*\.png$", re.IGNORECASE),
    ]
    ignore_names = {"graph_state.json"}

    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            name = file_path.name
            if name in ignore_names or any(p.match(name) for p in ignore_patterns):
                logfire.info(f"Ignoring auto-generated file: {name}")
                continue
            result.append(file_path.resolve())

    return result


async def list_working_directory_files(ctx: RunContext[ActionDeps]) -> List[str]:
    """
    List all files present in the working directory.

    Returns:
        List[str]: List of files in the working directory.
    """

    working_dir = ctx.deps.working_dir
    if not working_dir:
        raise ValueError("Working directory not initialized")

    result = get_file_list_in_control_execution_dir(working_dir)

    logfire.info(f"Working directory filteredfiles: {result}")
    return [str(p) for p in result]


list_working_directory_files_tool = Tool(list_working_directory_files, takes_ctx=True)
