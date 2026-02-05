from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State


@dataclass
class Start(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Initializing control environment")
        ctx.state.node_ind = ctx.deps.node_ind
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        try:
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output={}
            )
            logfire.info(f"Completed initial setup")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Start Node: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
