from pathlib import Path
from typing import Any, List, Optional
from uuid import UUID

import logfire
from alltrue.agents.schema.control_execution import (
    ComplianceJudgement,
    ComplianceStatus,
)
from pydantic_graph import BaseNode

from app.core.agents.action_prototype.pause.action import Pause
from app.core.agents.compliance_agent.agent import ComplianceAgent
from app.core.agents.compliance_agent.models import ComplianceInput, CompliantModel
from app.core.graph.deps.base_deps import ControlInfo
from app.core.graph.state.state import State
from app.core.models.models import ControlExecution
from app.core.storage_dependencies.repositories.providers import RepositoryProvider
from app.utils.file_upload.file_upload import upload_file


@logfire.instrument()
async def _perform_compliance_check(
    final_result: List[ComplianceInput],
    generated_files: List[Path],
    control_info: ControlInfo,
    control_exec_id: UUID,
    control_exec: ControlExecution,
    provider: RepositoryProvider,
    agent_messages: List[Any],
) -> tuple[ComplianceJudgement, Any]:
    """Perform compliance validation and upload evidence files.

    Flow: create container → load evidence → request response → parse judgement →
          upload evidence → optionally generate report → update status

    Args:
        final_result: The final result from graph execution
        generated_files: The file path of all the generated files from each action
        control_info: ControlInfo object containing control details
        control_exec_id: UUID of the control execution
        control_exec: ControlExecution object
        provider: Repository provider

    Returns:
        tuple containing:
            - ComplianceJudgement object with validation results
            - Original compliance result from the agent
    """
    logfire.info("Compliance Check: Starting compliance validation")
    agent = ComplianceAgent()
    control_compliance_result = None
    compliance_result = None

    try:
        # Steps A-F: Unified compliance validation and report generation
        compliance_result, report_result = await agent.validate_compliance_with_report(
            control_info.compliance_instruction,
            final_result,
            generated_files,
            generate_report=True,  # Always generate report for now
            report_title="Compliance Report",
            agent_messages=agent_messages,
        )

        # Step H: Upload evidence files referenced in compliance result
        non_compliant_evidence = []
        for file_path in compliance_result.non_compliant_evidence:
            try:
                non_compliant_evidence.append(
                    upload_file(
                        file_path,
                        {"control_exec_id": control_exec_id},
                        new_file_name=f"{control_exec_id}/{Path(file_path).name}",
                    )
                )
            except Exception as e:
                logfire.error(f"Failed to upload non-compliant evidence: {e}")

        compliant_evidence = []
        for file_path in compliance_result.compliant_evidence:
            try:
                compliant_evidence.append(
                    upload_file(
                        file_path,
                        {"control_exec_id": control_exec_id},
                        new_file_name=f"{control_exec_id}/{Path(file_path).name}",
                    )
                )
            except Exception as e:
                logfire.error(f"Failed to upload compliant evidence: {e}")

        # Create compliance judgement
        control_compliance_result = ComplianceJudgement(
            reasoning=compliance_result.reasoning,
            non_compliant_evidence=non_compliant_evidence,
            compliant_evidence=compliant_evidence,
        )

        # Step G: Handle report if generated
        if report_result:
            try:
                report_filename = Path(report_result.response_text.strip()).name
                downloaded_path = await agent.download_generated_report(
                    container_id=report_result.container_id,
                    report_filename=report_filename,
                    output_path=f"./UserData/{control_info.control_id}/{control_info.entity_id}/{control_info.control_execution_id}",
                )
                logfire.info(f"Report downloaded to: {downloaded_path}")

                # Upload the report
                control_compliance_result.report = upload_file(
                    downloaded_path,
                    {"control_exec_id": control_exec_id},
                    new_file_name=f"{control_exec_id}/report.docx",
                )
            except Exception as e:
                logfire.error(f"Failed to process report: {str(e)}")

    except Exception as e:
        # Construct error message
        error_message = f"Compliance check failed: {str(e)}"

        logfire.error(error_message)

        # Construct compliance_result if it doesn't exist
        if not compliance_result:
            compliance_result = CompliantModel(
                feedback=error_message,
                reasoning=error_message,
                non_compliant_evidence=[],
                compliant_evidence=[],
                answer="NON-COMPLIANT",
            )

        # Construct control_compliance_result if it doesn't exist
        if not control_compliance_result:
            control_compliance_result = ComplianceJudgement(
                reasoning=error_message,
                non_compliant_evidence=[],
                compliant_evidence=[],
            )

    # Step I: Update status (handles both success and error cases)
    if control_compliance_result and compliance_result:
        control_exec.output = control_compliance_result.model_dump()
        if compliance_result.answer == "COMPLIANT":
            control_exec.compliance_status = ComplianceStatus.COMPLIANT
            control_exec.mark_passed(control_compliance_result.model_dump())
        else:
            control_exec.compliance_status = ComplianceStatus.NON_COMPLIANT
            control_exec.mark_remediation_required(compliance_result.feedback)

    # Always update control execution and cleanup
    await provider.get_repository(ControlExecution).update(control_exec)
    await agent.cleanup()

    # Always return so UI can display the results
    return control_compliance_result, compliance_result


async def _generate_compliance_report(
    compliance_result: CompliantModel,
    control_info: ControlInfo,
    control_exec_id: UUID,
    control_exec: ControlExecution,
    control_compliance_result: ComplianceJudgement,
    provider: RepositoryProvider,
    report_result: Optional[Any] = None,
) -> None:
    """Generate compliance report and upload it.

    Args:
        compliance_result: The compliance validation result
        control_info: ControlInfo object containing control details
        control_exec_id: UUID of the control execution
        control_exec: ControlExecution object
        control_compliance_result: ComplianceJudgement object
        provider: Repository provider
        report_result: Optional report result from the unified agent
    """
    if report_result is None:
        logfire.info("No report result provided, skipping report generation")
        return

    logfire.info("Processing generated report")

    agent: Optional[ComplianceAgent] = None

    try:
        # Extract the report filename from the response
        # The AI should return just the filename in the response_text
        report_filename = report_result.response_text.strip()

        # Download the report using the unified agent
        agent = ComplianceAgent()
        downloaded_path = await agent.download_generated_report(
            container_id=report_result.container_id,
            report_filename=report_filename,
            output_path=f"./UserData/{control_info.control_id}/{control_info.entity_id}/{control_info.control_execution_id}",
        )

        logfire.info(f"Report successfully downloaded to: {downloaded_path}")

        # Upload the report
        control_compliance_result.report = upload_file(
            downloaded_path,
            {"control_exec_id": control_exec_id},
            new_file_name=f"{control_exec_id}/report.docx",
        )
        control_exec.output = control_compliance_result.model_dump()
        await provider.get_repository(ControlExecution).update(control_exec)

    except Exception as e:
        logfire.error(f"Failed to download report: {str(e)}")

    finally:
        # Clean up the container
        if agent is not None:
            await agent.cleanup()


async def _handle_skipped_compliance_check(
    uploaded_files: list,
    control_exec: ControlExecution,
    provider: RepositoryProvider,
) -> ComplianceJudgement:
    """Handle the case when compliance check is skipped.

    Args:
        uploaded_files: The uploaded files from the state
        control_info: ControlInfo object containing control details
        control_exec_id: UUID of the control execution
        control_exec: ControlExecution object
        provider: Repository provider

    Returns:
        ComplianceJudgement object with uploaded evidence
    """

    # Create a minimal compliance judgement for skipped checks
    control_compliance_result = ComplianceJudgement(
        reasoning="Compliance check was skipped as requested in the instruction",
        non_compliant_evidence=[],
        compliant_evidence=uploaded_files,
    )

    # Update control execution status to COMPLIANT
    control_exec.compliance_status = ComplianceStatus.COMPLIANT
    control_exec.mark_passed(control_compliance_result.model_dump())
    await provider.get_repository(ControlExecution).update(control_exec)

    return control_compliance_result


@logfire.instrument()
async def post_process_graph(
    graph_state: Optional[BaseNode],
    state: State,
    control_exec: ControlExecution,
    control_exec_id: UUID,
    control_info: ControlInfo,
    async_provider: RepositoryProvider,
):
    if graph_state and isinstance(graph_state, Pause):
        logfire.info("Graph execution paused. You can resume later.")
        return

    final_result = state.transform_to_compliance_input()
    logfire.info(
        f"Final Result: {final_result} -- Control Info: {control_info} -- Control Exec ID: {control_exec_id}"
    )

    # TODO: Currently use text to skip compliance check. We should have a compliance_action_type in the control execution schema
    if not control_info.compliance_instruction.strip().startswith(
        "**SKIP COMPLIANCE CHECK**"
    ):
        logfire.info("Graph execution completed. Performing compliance check.")
        # Perform compliance check and generate report in unified flow
        (
            control_compliance_result,
            compliance_result,
        ) = await _perform_compliance_check(
            final_result=final_result,
            generated_files=state.get_generated_files(),
            control_info=control_info,
            control_exec_id=control_exec_id,
            control_exec=control_exec,
            provider=async_provider,
            agent_messages=state.agent_messages,
        )
    else:
        logfire.info("Skipping compliance check as per instruction.")
        uploaded_files = state.get_uploaded_files()

        # Skip compliance check but still update status to COMPLIANT
        control_compliance_result = await _handle_skipped_compliance_check(
            uploaded_files,
            control_exec,
            async_provider,
        )
    logfire.info("State cleared for next round.")
