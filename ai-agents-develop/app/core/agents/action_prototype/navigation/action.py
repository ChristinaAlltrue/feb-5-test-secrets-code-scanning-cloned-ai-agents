from dataclasses import dataclass
from typing import Literal

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic import BaseModel, Field
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.navigation.schema import (
    NavigationDeps,
    NavigationOutput,
)
from app.core.agents.action_prototype.navigation.tool import navigation
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


class GeneralResponse(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description=f"yes or no, whether the navigation was successful"
    )
    feedback: str


@dataclass
class Navigation(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running navigation action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()
        action_deps = ctx.deps.get_action_deps()

        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None
        try:
            current_deps = NavigationDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                res = await navigation(
                    new_ctx,
                    current_deps.instructions,
                    current_deps.goal,
                    current_deps.initial_url,
                )
            # ==== end logic ====

            result = NavigationOutput.model_validate(res)
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            logfire.info(f"Output: {result_dict}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Navigation action: {e}")
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the Navigation Agent",
                    "reason": str(e),
                }
            await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
