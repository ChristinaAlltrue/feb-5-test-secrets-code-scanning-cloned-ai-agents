from dataclasses import dataclass
from pprint import pformat

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.schema import (
    AuditAnalysisConnectedNodeDepsPart2,
)
from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.tool import (
    run_connected_agent_part2,
)
from app.core.agents.action_prototype.pause.action import Pause
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.exceptions.control_exceptions import PauseExecution


@dataclass
class AuditAnalysisConnectedAgentsPart2(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info(str(ctx.state.data))
        logfire.info("Running AuditAnalysisConnectedAgentsPart2 action")
        # input("Please copy state ....")
        ctx.state.node_ind = ctx.deps.node_ind

        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps(
                allowed_domains=["https://ghco-dev.archerirm.us"]
            )

        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        logfire.info("pprint(action_deps)")
        logfire.info(pformat(action_deps))

        logfire.info("pprint(current_deps)")
        logfire.info(pformat(ctx.deps.get_current_deps(ctx.state.output)))
        # input("Please copy deps ....")
        try:
            # raise PauseExecution(
            #     {
            #         "reason": "Paused for manual verification"
            #     }
            # )
            raw_deps = ctx.deps.get_current_deps(ctx.state.output)

            if "provisioning_instructions" not in raw_deps:
                logfire.warning(
                    "provisioning_instructions not in raw_deps, using user_list_instructions instead"
                )
                current_deps = AuditAnalysisConnectedNodeDepsPart2.model_validate(
                    # ctx.deps.get_current_deps(ctx.state.output)
                    {
                        "provisioning_instructions": raw_deps[
                            "user_list_instructions"
                        ],  # TODO: fix input schema problem (not getting provisioning_instructions)
                        **raw_deps,
                    }
                )
            else:
                logfire.info("provisioning_instructions found in raw_deps")
                current_deps = AuditAnalysisConnectedNodeDepsPart2.model_validate(
                    raw_deps
                )

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await run_connected_agent_part2(
                    new_ctx,
                    task_description=current_deps.task_description,
                    homepage_url=current_deps.homepage_url,
                    username=current_deps.username,
                    password=current_deps.password,
                    bu_contact=current_deps.bu_contact,
                    software_list_string=current_deps.software_list,
                    target_business_unit=current_deps.target_business_unit,
                    google_token=current_deps.google_token,
                    provisioning_instructions=current_deps.provisioning_instructions,
                )

            result_dict = result.model_dump()

            result_with_feedback = await store_action_execution(result_dict, ctx)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            logfire.info(
                f"AuditAnalysisConnectedAgent completed successfully: {result_with_feedback}"
            )
            return await ctx.deps.get_next_node()

        except PauseExecution as pause_exc:
            logfire.info(
                f"AuditAnalysisConnectedAgent execution paused: {pause_exc.data}"
            )
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED,
                error=f"Execution Paused: {pause_exc.data}",
            )
            return Pause(paused_at=self.__class__.__name__)

        except Exception as e:
            logfire.error(f"AuditAnalysisConnectedAgent failed: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
