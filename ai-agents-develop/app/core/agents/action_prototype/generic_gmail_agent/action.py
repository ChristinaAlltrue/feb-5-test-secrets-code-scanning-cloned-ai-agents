from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.generic_gmail_agent.schema import (
    GenericGmailAgentDeps,
    GenericGmailAgentOutput,
)
from app.core.agents.action_prototype.generic_gmail_agent.tool import (
    generic_gmail_agent_tool,
)
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class GenericGmailAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running GenericGmailAgent action")
        # 1. Update the node index
        ctx.state.node_ind = ctx.deps.node_ind
        # 2. Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            # 3. Get the current deps and validate it
            current_deps = GenericGmailAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")
            if len(current_deps.credentials) == 0:
                raise ValueError("No credentials provided for GenericGmailAgent")
            else:
                google_token_key_name = list(current_deps.credentials.keys())[0]

            # 4. Run the logic
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                new_ctx.deps.credentials = current_deps.credentials
                res = await generic_gmail_agent_tool(
                    new_ctx, current_deps.goal, google_token_key_name
                )

            # 5. Store the output
            result = GenericGmailAgentOutput(output=res)
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
            logfire.error(f"Error in GenericGmailAgent action: {e}")
            # 8. Handle errors and update the action status to failed
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
