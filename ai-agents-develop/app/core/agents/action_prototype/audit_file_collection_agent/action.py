from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.audit_file_collection_agent.schema import (
    FileCollectionAgentNodeDeps,
)
from app.core.agents.action_prototype.audit_file_collection_agent.tool import (
    run_file_collection_agent,
)
from app.core.agents.action_prototype.pause.action import Pause
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.exceptions.control_exceptions import PauseExecution
from app.utils.file_upload.file_upload import upload_file


@dataclass
class FileCollectionAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running FileCollectionAgent action")
        ctx.state.node_ind = ctx.deps.node_ind

        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps(
                allowed_domains=["https://ghco-dev.archerirm.us"]
            )

        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            current_deps = FileCollectionAgentNodeDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await run_file_collection_agent(
                    ctx,
                    task_description="TODO: add task description in the input schema",
                    homepage_url=current_deps.homepage_url,
                    username=current_deps.username,
                    password=current_deps.password,
                    bu_contact=current_deps.bu_contact,
                    software_list_string=current_deps.software_list,
                    target_business_unit=current_deps.target_business_unit,
                    google_token=current_deps.google_token,
                )

            uploads = []
            for evidence in result.evidence:
                try:
                    uploads.append(
                        upload_file(
                            evidence.path,
                            {
                                "control_exec_id": ctx.deps.control_info.control_execution_id
                            },
                        )
                    )
                except Exception as ex:
                    logfire.error(
                        "Unexpected error uploading evidence; skipping",
                        error=str(ex),
                        evidence=evidence.path,
                    )

            result.model_extra["upload_evidence"] = uploads

            result_dict = result.model_dump()

            result_with_feedback = await store_action_execution(result_dict, ctx)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            logfire.info(
                f"FileCollectionAgent completed successfully: {result_with_feedback}"
            )
            return await ctx.deps.get_next_node()

        except PauseExecution as pause_exc:
            logfire.info(f"FileCollectionAgent execution paused: {pause_exc.data}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED,
                error=f"Execution Paused: {pause_exc.data}",
            )
            return Pause(paused_at=self.__class__.__name__)

        except Exception as e:
            logfire.error(f"FileCollectionAgent failed: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
