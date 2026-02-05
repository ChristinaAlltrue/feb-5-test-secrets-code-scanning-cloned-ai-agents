from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.github_auditor.schema import (
    GithubPRAuditorAgentDeps,
)
from app.core.agents.action_prototype.github_auditor.tool import github_pr_auditor
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class GithubPRAuditorAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running GithubPRAuditorAgent action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = {}
        try:
            current_deps = GithubPRAuditorAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await github_pr_auditor(
                    ctx=new_ctx,
                    target_PR=current_deps.target_PR,
                    github_token=current_deps.github_token,
                    goal=current_deps.goal,
                )
            # ==== end logic ====
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED,
                output=result_with_feedback,
            )
            logfire.info(f"Output: {ctx.state.output}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"GithubPRAuditorAgent failed: {e}")
            if result_dict == {}:
                result_dict = {
                    "feedback": "Problem running the GithubPRAuditorAgent",
                    "reason": str(e),
                }
            await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
