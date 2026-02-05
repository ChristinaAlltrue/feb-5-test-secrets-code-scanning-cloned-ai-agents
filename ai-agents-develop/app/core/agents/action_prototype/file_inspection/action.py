from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_ai import Agent
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.file_inspection.schema import (
    FileInspectionDeps,
    FileInspectionOutput,
)
from app.core.agents.action_prototype.file_inspection.tools import file_process
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class FileInspectionNodeException(Exception):
    """Custom exception raised for errors in the file inspection node."""


@dataclass
class FileInspection(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running file inspection action")
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()

        action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        try:
            current_deps = FileInspectionDeps.model_validate(
                ctx.deps.get_current_deps()
            )
            logfire.info(f"Input: {current_deps}")

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                agent = Agent(
                    model=get_pydanticai_openai_llm(),
                    tools=[file_process],
                    deps_type=FileInspectionDeps,
                    deps=current_deps,
                    output_type=FileInspectionOutput,
                    system_prompt="""
                    You will receive a list of files.
                    Your tasks are:

                    1. **Categorize the files based on their filenames.**
                    - Files with similar patterns or belonging to the same group should be grouped together.
                    - For example, if there are "companyA-202401.csv", "companyA-202402.csv", group them as 'companyA'.

                    2. Analyze the requirements from the users and generate a prompt for the agent tool `file_process` to process the files.

                    2. **For each category**, call the `file_process` tool **separately** with the relevant files in that group.

                    If you receive any unclear or ambiguous filenames, ask for clarification.

                    Output should follow the required output schema.
                    """,
                )
                user_prompt = f"""
                You are a helpful assistant that process the files based on the requirements from the users.
                The files are:
                {current_deps.file_path_list}
                The instructions are:
                {current_deps.instructions}

                """
                res = await agent.run(user_prompt, deps=new_ctx.deps)
            logfire.info(f"Result: {res}")

            result = FileInspectionOutput.model_validate(res)
            result = result.model_dump()
            ctx.state.store_output(result)

            # Update the action status to success, also store the output
            action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result
            )

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in File inspectio action: {e}")
            action_deps.update_action_status(ActionExecutionStatus.FAILED, error=str(e))
            raise FileInspectionNodeException(
                f"File inspection Node failed: {e}"
            ) from e
