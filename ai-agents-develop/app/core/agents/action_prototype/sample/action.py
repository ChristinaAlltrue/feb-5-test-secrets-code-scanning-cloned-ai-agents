from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.sample.schema import SampleDeps, SampleOutput
from app.core.agents.action_prototype.sample.tool import sample
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State

"""
This is a sample action that demonstrates the use of the graph deps.
Follow the steps below to implement your own action:
1. Update the node index in the state
2. Update the action status to running
3. Get the current deps and validate it
4. Run the logic
5. Store the output
6. Update the action status to success or failed
7. Return the next node
8. Handle errors and update the action status to failed
"""


@dataclass
class Sample(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running sample action")
        # 1. Update the node index
        ctx.state.node_ind = ctx.deps.node_ind
        # 2. Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            # 3. Get the current deps and validate it
            current_deps = SampleDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            # 4. Run the logic
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                res = await sample(new_ctx, current_deps.input)

            # 5. Store the output
            result = SampleOutput(output=res)
            result = result.model_dump()
            ctx.state.store_output(result)

            # 6. Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result
            )
            logfire.info(f"Output: {ctx.state.output}")

            # 7. Return the next node
            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Sample action: {e}")
            # 8. Handle errors and update the action status to failed
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
