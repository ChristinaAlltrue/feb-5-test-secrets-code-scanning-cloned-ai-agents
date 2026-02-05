from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.GHCO_auditor.schema import GHCOAuditorDeps
from app.core.agents.action_prototype.GHCO_auditor.tool import GHCO_auditor
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.utils.file_upload.file_upload import upload_file


@dataclass
class GHCOAuditor(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running GHCOAuditor action")
        ctx.state.node_ind = ctx.deps.node_ind

        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps(
                allowed_domains=["https://ghco-dev.archerirm.us"]
            )
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        try:
            current_deps = GHCOAuditorDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            # === logic ===
            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await GHCO_auditor(
                    new_ctx,
                    target_business_unit=current_deps.target_business_unit,
                    login_url=current_deps.login_url,
                    navigation_instruction=current_deps.navigation_instruction,
                    username=current_deps.username,
                    password=current_deps.password,
                )
            # ==== end logic ====
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
            result = result.model_dump()
            ctx.state.store_output(result)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result
            )
            logfire.info(f"Output: {ctx.state.output}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"GHCOAuditor failed: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
