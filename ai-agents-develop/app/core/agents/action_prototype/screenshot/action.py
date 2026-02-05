from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.screenshot.schema import ScreenshotDeps
from app.core.agents.action_prototype.screenshot.tools import start_screen_agent
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


class ScreenshotNodeException(Exception):
    """Custom exception raised for errors in the screenshot node."""


@dataclass
class ScreenshotAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running screenshot action")

        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None
        try:
            current_deps = ScreenshotDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await start_screen_agent(
                    new_ctx,
                    target_url=current_deps.target_url,
                    target_information=current_deps.target_information,
                )
            # ==== end logic ====
            # Store the output in the state
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Screenshot action: {e}")
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the Screenshot Agent",
                    "reason": str(e),
                }
            await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
