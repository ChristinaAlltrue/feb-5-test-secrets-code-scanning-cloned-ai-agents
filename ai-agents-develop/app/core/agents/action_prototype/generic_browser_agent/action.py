from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.generic_browser_agent.generic_browser_agent import (
    generic_browser_agent,
)
from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentActionOutput,
    GenericBrowserAgentDeps,
)
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class GenericBrowserAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running Generic Browser Agent Action")
        ctx.state.node_ind = ctx.deps.node_ind

        # Initialize browser deps if needed
        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()

        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None

        try:
            current_deps = GenericBrowserAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                res = await generic_browser_agent(
                    ctx=new_ctx,
                    task=current_deps.task,
                    max_steps=current_deps.max_steps,
                    model_name=current_deps.model_name,
                    use_vision=current_deps.use_vision,
                    excluded_actions=current_deps.excluded_actions,
                )
            logfire.info(f"Result: {res}")

            result = GenericBrowserAgentActionOutput.model_validate(res)
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )

            logfire.info(f"Output: {result_with_feedback}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Generic Browser Agent Action: {e}")
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the Generic Browser Agent",
                    "reason": str(e),
                }
            result_with_feedback = await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
