from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_ai import Agent
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.sheet_compare.schema import (
    SheetCompareDeps,
    SheetCompareOutput,
)
from app.core.agents.action_prototype.sheet_compare.tools import compare_sheets
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


@dataclass
class SheetCompare(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running sheet compare action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()

        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        try:
            current_deps = SheetCompareDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                agent = Agent(
                    model=get_pydanticai_openai_llm(),
                    tools=[compare_sheets],
                    deps_type=SheetCompareDeps,
                    deps=current_deps,
                    output_type=SheetCompareOutput,
                    system_prompt="""
                    You will receive a list of files.
                    Your tasks are:

                    1. **Categorize the files based on their filenames.**
                    - Files with similar patterns or belonging to the same group should be grouped together.
                    - For example, if there are "companyA-202401.csv", "companyA-202402.csv", group them as 'companyA'.

                    2. **For each category**, call the `compare_sheets` tool **separately** with the relevant files in that group.

                    3. **Do not mix unrelated files** in the same comparison.

                    4. For each comparison, provide a brief explanation of how you grouped the files and your reasoning.

                    If you receive any unclear or ambiguous filenames, ask for clarification.

                    Output should follow the required output schema.
                    """,
                )
                user_prompt = f"""
                You are a helpful assistant that compares two sheets and returns the differences.
                The sheets are:
                {current_deps.file_path_list}
                The instructions are:
                {current_deps.instructions}

                """
                res = await agent.run(user_prompt, deps=new_ctx.deps)
            logfire.info(f"Result: {res}")

            result = SheetCompareOutput.model_validate(res)
            result = result.model_dump()
            ctx.state.store_output(result)

            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result
            )

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Sheet compare action: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
