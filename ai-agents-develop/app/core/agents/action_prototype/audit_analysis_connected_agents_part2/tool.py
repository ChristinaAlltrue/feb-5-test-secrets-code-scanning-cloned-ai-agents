import logfire
from pydantic import SecretStr
from pydantic_graph import GraphRunContext

from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.schema import (
    AuditAnalysisConnectedAgentOutputPart2,
)
from app.core.agents.action_prototype.audit_file_collection_agent.tool import (
    run_file_collection_agent,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.audit_analysis_agent import (
    TARGET_OUTPUT,
    audit_analysis_agent,
)
from app.core.agents.utils.type_utils import EvidenceItem, evidences2files
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State
from app.exceptions.control_exceptions import PauseExecution


async def run_connected_agent_part2(
    ctx: GraphRunContext[State, GraphDeps],
    task_description: str,
    homepage_url: str,
    username: str,
    password: str,
    bu_contact: str,
    software_list_string: str,
    target_business_unit: str,
    google_token: SecretStr,
    provisioning_instructions: str,
) -> AuditAnalysisConnectedAgentOutputPart2:
    """Main function to connect request agent and analysis agent. Be aware that only request agent will pause and resume, history of this class == history of request agent"""
    logfire.info("Starting run_connected_agent_part2")

    try:
        logfire.info("Running run_file_collection_agent")
        user_list_request_agent_result = await run_file_collection_agent(
            ctx,
            task_description=f"Previous step output: {ctx.state.data}\n\n{task_description}",
            homepage_url=homepage_url,
            username=username,
            password=password,
            bu_contact=bu_contact,
            software_list_string=software_list_string,
            target_business_unit=target_business_unit,
            google_token=google_token,
        )

        files_downloaded = evidences2files(user_list_request_agent_result.evidence)
        software_list = user_list_request_agent_result.softwares

        user_list_sampling_analysis_agent_result = await audit_analysis_agent(
            ctx,
            report_instructions=provisioning_instructions,
            software_list=software_list,
            files_to_upload=files_downloaded,
            target_output=TARGET_OUTPUT.PROVISIONING,
        )

        combined_result = AuditAnalysisConnectedAgentOutputPart2(
            **vars(user_list_request_agent_result),
            analysis_agent_feedback=user_list_sampling_analysis_agent_result.feedback,
            analysis_agent_generated_file=user_list_sampling_analysis_agent_result.generated_file,
            request_agent_downloaded_files=evidences2files(
                user_list_request_agent_result.evidence
            ),
        )
        combined_result.evidence = (
            [
                EvidenceItem(
                    object_type="file",
                    path=user_list_sampling_analysis_agent_result.generated_file,
                )
            ]
            if user_list_sampling_analysis_agent_result.generated_file
            else []
        )

        return combined_result
    except PauseExecution as pause_exc:
        raise pause_exc
