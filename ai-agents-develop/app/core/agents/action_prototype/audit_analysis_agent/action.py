from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.audit_analysis_agent.schema import (
    AuditAnalysisAgentDeps,
    AuditAnalysisAgentOutput,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.audit_analysis_agent import (
    audit_analysis_agent,
)
from app.core.agents.compliance_agent.models import EvidenceItem
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class AuditAnalysisAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running Audit Analysis Agent")
        ctx.state.node_ind = ctx.deps.node_ind

        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            current_deps = AuditAnalysisAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Audit Analysis Agent Input: {current_deps}")

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                result = await audit_analysis_agent(
                    new_ctx,
                    report_instructions=current_deps.report_instructions,
                    software_list=current_deps.softwares,
                    files_to_upload=current_deps.files_to_upload,
                )

            logfire.info(f"Audit Analysis Agent Result: {result}")

            # Create evidence items
            evidence_items = []
            if result.generated_file:
                evidence_items.append(
                    EvidenceItem(
                        path=result.generated_file,
                        object_type="file",
                    )
                )

            # Process input files as evidence if they exist
            if current_deps.files_to_upload:
                for file_path in current_deps.files_to_upload:
                    evidence_items.append(
                        EvidenceItem(
                            path=file_path,
                            object_type="file",
                        )
                    )

            # Create final output
            analysis_output = AuditAnalysisAgentOutput(
                successful=result.successful,
                feedback=result.feedback,
                generated_file=result.generated_file,
                softwares_analyzed=current_deps.softwares,
                files_processed=current_deps.files_to_upload or [],
                evidence=evidence_items,
            )

            result_dict = analysis_output.model_dump()
            ctx.state.store_output(result_dict)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_dict
            )

            logfire.info(f"Audit Analysis Agent Output: {result_dict}")
            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Audit Analysis Agent failed: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
