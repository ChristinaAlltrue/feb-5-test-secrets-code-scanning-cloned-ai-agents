from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.general_browser.schema import (
    GeneralBrowserDeps,
    GeneralBrowserOutput,
)
from app.core.agents.action_prototype.general_browser.tool import general_browser
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


class GeneralBrowserNodeException(Exception):
    """Custom exception raised for errors in the GeneralBrowser node."""


@dataclass
class GeneralBrowser(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running general browser action")
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()

        action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            current_deps = GeneralBrowserDeps.model_validate(
                ctx.deps.get_current_deps()
            )
            logfire.info(f"Input: {current_deps}")

            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                res = await general_browser(
                    new_ctx,
                    current_deps.instructions,
                    current_deps.goal,
                    current_deps.initial_url,
                    current_deps.target_information,
                )
            # ==== end logic ====

            result = GeneralBrowserOutput.model_validate(res)
            result = result.model_dump()
            ctx.state.store_output(result)

            # Update the action status to success, also store the output
            action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result
            )
            logfire.info(f"Output: {ctx.state.output}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in GeneralBrowser action: {e}")
            action_deps.update_action_status(ActionExecutionStatus.FAILED, error=str(e))
            raise GeneralBrowserNodeException(f"GeneralBrowser Node failed: {e}") from e
