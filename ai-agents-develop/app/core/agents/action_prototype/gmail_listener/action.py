from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus, PlainTextLog
from pydantic_graph import BaseNode, GraphRunContext

from app.api.services.control_execution_service import (
    create_delayed_control_execution_job,
)
from app.core.agents.action_prototype.gmail_listener.schema import (
    GmailListenerAgentDeps,
)
from app.core.agents.action_prototype.gmail_listener.tool import gmail_listener
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.utils.scheduler.exception import ReschduledJobException


@dataclass
class GmailListenerAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running GmailListenerAgent action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = {}
        try:
            current_deps = GmailListenerAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await gmail_listener(
                    ctx=new_ctx,
                    google_token=current_deps.google_token,
                    goal=current_deps.goal,
                )
            # ==== end logic ====
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)

            # Handle scheduler job based on trigger result
            control_execution_id = ctx.deps.control_info.control_execution_id
            if result_dict.get("trigger") == "no":
                await action_deps.add_log(
                    PlainTextLog(
                        data=f"Condition not satisfied, scheduling a delayed job to run again. Reason: {result_dict.get('feedback')}"
                    )
                )
                # Register a delayed job to rerun this control execution after 15 seconds

                job_id = create_delayed_control_execution_job(
                    control_execution_id,
                    credentials=ctx.deps.credentials,
                    delay_seconds=15,
                )
                logfire.info(
                    "Registered delayed job for Gmail listener with 'no' trigger",
                    control_execution_id=str(control_execution_id),
                    job_id=job_id,
                    delay_seconds=15,
                )
                raise ReschduledJobException(
                    "Condition not satisfied, scheduling a delayed job to run again"
                )
            elif result_dict.get("trigger") == "yes":
                await action_deps.add_log(
                    PlainTextLog(
                        data=f"Condition satisfied. Reason: {result_dict.get('feedback')}"
                    )
                )
                logfire.info("Condition satisfied")

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED,
                output=result_with_feedback,
            )
            logfire.info(f"Output: {ctx.state.output}")

            return await ctx.deps.get_next_node()

        except ReschduledJobException as e:
            # TODO: make a new status for rescheduled job
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise

        except Exception as e:
            logfire.error(f"GmailListenerAgent failed: {e}")
            if result_dict == {}:
                result_dict = {
                    "trigger": "no",
                    "feedback": f"Problem running the GmailListenerAgent: {str(e)}",
                }
            await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
