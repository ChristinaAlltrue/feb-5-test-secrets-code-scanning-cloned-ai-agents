import json
import uuid
from pathlib import Path
from typing import List, Optional

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from app.core.agents.action_prototype.utils import format_model_messages
from app.core.agents.compliance_agent.models import (
    ComplianceInput,
    CompliantModel,
    ContainerFile,
    ReportGenerationResult,
    UploadedFile,
)
from app.core.agents.utils.openai_utils.container import (
    create_response_with_container,
    delete_container,
    download_specific_file,
    find_file_in_container,
    get_or_create_container,
    upload_files_to_container,
)
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

COMPLIANCE_MODEL_NAME = "o3"
REPORT_MODEL_NAME = "o4-mini"


class ComplianceAgent:
    def __init__(self):
        if OPENAI_API_KEY is None:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please set it in your environment variables."
            )

        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.container = None
        self.uploaded_files: List[UploadedFile] = []

    async def validate_compliance_with_report(
        self,
        compliance_instruction: str,
        control_output: List[ComplianceInput],
        generated_files: List[Path],
        generate_report: bool = False,
        report_title: str = "Compliance Report",
        agent_messages: Optional[List[ModelMessage]] = None,
    ) -> tuple[CompliantModel, Optional[ReportGenerationResult]]:
        """
        Unified compliance validation and optional report generation.

        Flow: create container → load evidence → request response → parse judgement →
              upload evidence → optionally generate report → update status

        Args:
            compliance_instruction: The compliance rule to validate against
            control_output: The output data to validate
            generated_files: The file path of all the generated files from each action
            generate_report: Whether to generate a report after compliance validation
            report_title: Title for the generated report

        Returns:
            tuple containing:
                - CompliantModel with validation results
                - Optional ReportGenerationResult if report was generated
        """
        try:
            # Step A: Create container
            logfire.info("Creating container for compliance validation")
            self.container = await get_or_create_container(
                self.client, name=f"compliance-agent-{uuid.uuid4()}"
            )
            logfire.info(f"Container created: {self.container.id}")

            # Step B: Upload all evidence files to container
            if generated_files:
                logfire.info(f"Uploading {len(generated_files)} generated files")
                file_ids = await self._upload_evidence_files(generated_files)
                logfire.info(f"Uploaded {len(file_ids)} files to container")
            else:
                logfire.info("No files to upload")

            # Step C: Create compliance judgement prompt
            prompt = self._create_compliance_prompt(
                compliance_instruction, control_output, agent_messages
            )

            # Step D: Request compliance judgement from container
            logfire.info("Requesting compliance judgement from container")
            response = await create_response_with_container(
                self.client, self.container.id, prompt, model=COMPLIANCE_MODEL_NAME
            )

            # Step E: Parse the response to extract compliance judgement
            compliance_result = await self._parse_compliance_response(
                response.output_text
            )

            # Step F: Decide whether to generate report
            report_result = None
            if generate_report:
                logfire.info("Generating compliance report")
                report_result = await self._generate_report(
                    compliance_result, report_title
                )

            return compliance_result, report_result

        except Exception as e:
            logfire.error(f"Compliance validation failed: {str(e)}")
            raise

    async def _upload_evidence_files(self, file_paths: List[Path]) -> List[str]:
        """
        Upload evidence files to the container.
        - Exclude the screenshot files.
        """
        if not self.container:
            raise Exception("Container not created")

        # exclude the screenshot files
        filtered_file_paths: List[Path] = []
        for file in file_paths:
            if not (file.name.startswith("page-") and file.suffix == ".png"):
                filtered_file_paths.append(file)

        file_ids = await upload_files_to_container(
            self.client, self.container.id, filtered_file_paths
        )

        for i, path in enumerate(filtered_file_paths):
            self.uploaded_files.append(
                UploadedFile(
                    original_path=str(path), file_id=file_ids[i], file_name=path.name
                )
            )

        return file_ids

    def _create_compliance_prompt(
        self,
        compliance_instruction: str,
        control_output: List[ComplianceInput],
        agent_messages: Optional[List[ModelMessage]] = None,
    ) -> str:
        """Create the prompt for compliance judgement."""
        # Prepare evidence summary
        uploaded_files_list = "\n".join(
            [
                f"- file name: {file.file_name}, path: {file.original_path}"
                for file in self.uploaded_files
            ]
        )
        if not uploaded_files_list:
            uploaded_files_list = "No uploaded files provided"

        # Prepare agent messages history
        if agent_messages:
            agent_history_list = [
                "\n\nAGENT CONVERSATION HISTORY:\n<agent_history_start>"
            ]
            agent_history_list.extend(format_model_messages(agent_messages))
            agent_history_list.append("<agent_history_end>\n")
            agent_history = "\n".join(agent_history_list)
        else:
            agent_history = ""

        prompt = f"""
You are a compliance validator. Your task is to evaluate whether the given result complies with a specified compliance rule.

COMPLIANCE RULE:
{compliance_instruction}

RESULT DATA:
{json.dumps([item.model_dump() for item in control_output], indent=2)}

EVIDENCE FILES AVAILABLE:
{uploaded_files_list}{agent_history}

Please analyze the result data and evidence against the compliance rule. Provide your response in the following JSON format:

{{
    "answer": "COMPLIANT" or "NON-COMPLIANT",
    "reasoning": "Detailed reasoning about your analysis",
    "feedback": "Short feedback for remediation if non-compliant",
    "compliant_evidence": [<list of compliant evidence file paths, can be empty>],
    "non_compliant_evidence": [<list of non-compliant evidence file paths, can be empty>]
}}

- The reasoning should be really detailed and thorough.
- All the fields are required,
Focus on the evidence provided and how it relates to the compliance rule.
"""
        return prompt

    async def _parse_compliance_response(self, response_text: str) -> CompliantModel:
        """
        Parse the container response to extract compliance judgement using an agent.
        """
        # Use a Pydantic AI agent to parse the response and generate a proper CompliantModel
        agent = Agent(
            model=get_pydanticai_openai_llm(model_name="gpt-4.1"),
            output_type=CompliantModel,
            system_prompt="""
                You are a compliance validator. Your task is to parse the given compliance analysis response
                and extract the compliance judgement into a structured format.
                Return a properly structured CompliantModel with all the required fields.
                The evidence file should be the path, not just the file name.
                And you have to pick up the file path from EVIDENCE FILES PATHS, in the response text, it could be the file path in the sandbox, which is not the file path in the original evidence files.
            """,
        )

        # Create a prompt for the agent to parse the response
        prompt = f"""
Please parse this compliance analysis response and extract the compliance judgement:

RESPONSE TEXT:
{response_text}

EVIDENCE FILES PATHS:
{chr(10).join([f'- file name: {file.file_name}, path: {file.original_path}' for file in self.uploaded_files])}

"""

        try:
            # Use the agent to parse the response
            result = await agent.run(prompt)
            logfire.info(
                f"Successfully parsed compliance response: {result.output!r}",
            )
            return result.output
        except Exception as e:
            logfire.error(f"Failed to parse compliance response with agent: {e}")
            # Fallback to a basic response
            return CompliantModel(
                answer="NON-COMPLIANT",
                reasoning=(
                    response_text[:500] + "..."
                    if len(response_text) > 500
                    else response_text
                ),
                feedback="Unable to parse response properly",
                compliant_evidence=[],
                non_compliant_evidence=[],
            )

    async def _generate_report(
        self, compliance_result: CompliantModel, report_title: str
    ) -> ReportGenerationResult:
        """Generate a report using the container."""
        if not self.container:
            raise Exception("Container not created")

        prompt = f"""
You are a professional report generator. Create a comprehensive DOCX report based on the existing compliance validation analysis.

REPORT TITLE: {report_title}

EXISTING COMPLIANCE ANALYSIS:
- Compliance Status: {compliance_result.answer}
- Reasoning: {compliance_result.reasoning}
- Compliant Evidence: {', '.join(compliance_result.compliant_evidence) if compliance_result.compliant_evidence else 'None'}
- Non-Compliant Evidence: {', '.join(compliance_result.non_compliant_evidence) if compliance_result.non_compliant_evidence else 'None'}

EVIDENCE FILES AVAILABLE:
{chr(10).join([f"- {file.file_name}" for file in self.uploaded_files])}

Please create a professional DOCX report that includes:
1. Executive Summary (based on the compliance status)
2. Detailed Analysis (using the existing reasoning)
3. Key Findings (from the compliance validation)
4. Recommendations (if applicable)
5. Appendices with relevant evidence

The report should be well-structured, professional, and comprehensive, building upon the existing compliance analysis rather than re-analyzing the evidence.
Then you just return the file name of the report, no other text.
"""

        response = await create_response_with_container(
            self.client, self.container.id, prompt, model=REPORT_MODEL_NAME
        )

        return ReportGenerationResult(
            container_id=self.container.id,
            report_generated=True,
            response_text=response.output_text,
            uploaded_files=self.uploaded_files,
        )

    async def download_generated_report(
        self, container_id: str, report_filename: str, output_path: str
    ) -> str:
        """Download a generated report from the container."""
        try:
            # Find the report file
            report_file = await self.find_report_file(container_id, report_filename)
            if not report_file:
                raise Exception(
                    f"Report file '{report_filename}' not found in container"
                )
            safe_name = Path(report_filename).name
            # Download the report
            downloaded_path = await self.download_report(
                container_id, report_file.id, Path(output_path) / safe_name
            )
            return downloaded_path

        except Exception as e:
            raise Exception(f"Failed to download generated report: {str(e)}")

    async def find_report_file(
        self, container_id: str, report_filename: str
    ) -> Optional[ContainerFile]:
        """Find a specific file in the container by filename."""
        try:
            file_data = await find_file_in_container(
                self.client, container_id, report_filename
            )
            return ContainerFile(**file_data) if file_data else None
        except Exception as e:
            raise Exception(f"Failed to find report file: {str(e)}")

    async def download_report(
        self, container_id: str, file_id: str, output_path: Path
    ) -> str:
        """Download a file from the container."""
        try:
            # Download the file
            downloaded_path = await download_specific_file(
                self.client, container_id, file_id, output_path
            )
            return downloaded_path

        except Exception as e:
            raise Exception(f"Failed to download report: {str(e)}")

    async def cleanup(self):
        """Clean up the container."""
        if self.container:
            try:
                await delete_container(self.client, self.container.id)
                logfire.info(f"Container {self.container.id} cleanup completed")
            except Exception as e:
                logfire.warning(f"Cleanup warning: {str(e)}")
