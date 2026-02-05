from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.login.schema import LoginDeps
from app.core.agents.action_prototype.login.tool import login
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class LoginAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running login action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running

        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()

        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None
        try:
            current_deps = LoginDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await login(
                    new_ctx,
                    initial_url=current_deps.initial_url,
                    username=current_deps.username,
                    password=current_deps.password,
                    instructions=current_deps.instructions,
                    mfa_secret=current_deps.mfa_secret,
                    max_steps=current_deps.max_steps,
                )
            # ==== end logic ====

            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            logfire.info(f"Output: {ctx.state.output}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the Login Agent",
                    "reason": str(e),
                }
            await store_action_execution(result_dict, ctx)
            logfire.error(f"Error in Login action: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
