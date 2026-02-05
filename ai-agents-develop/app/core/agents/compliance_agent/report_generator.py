from pathlib import Path
from typing import List, Optional

import logfire
from openai import AsyncOpenAI

from app.core.agents.compliance_agent.models import (
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
    list_container_files,
    upload_files_to_container,
)
from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

MODEL_NAME = "o4-mini"


class ReportGenerator:
    def __init__(self):
        if OPENAI_API_KEY is None:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please set it in your environment variables."
            )
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.container = None
        self.uploaded_files: List[UploadedFile] = []

    async def create_container(self, name: str = "report-generator") -> str:
        """
        Step 1: Create a container for file operations
        """
        try:
            self.container = await get_or_create_container(self.client, name=name)
            return self.container.id
        except Exception as e:
            raise Exception(f"Failed to create container: {str(e)}")

    async def upload_evidence(self, file_paths: List[str]) -> List[str]:
        """
        Step 2: Upload evidence files to the container
        """
        if not self.container:
            raise Exception("Container not created. Call create_container() first.")

        # Convert string paths to Path objects and filter existing files
        valid_paths = []
        for file_path in file_paths:
            path = Path(file_path).resolve()
            if path.exists() and path.is_file():
                valid_paths.append(path)
            else:
                logfire.warning(
                    f"Warning: File not found or not accessible: {file_path}"
                )
        if len(valid_paths) > 0:
            file_ids = await upload_files_to_container(
                self.client, self.container.id, valid_paths
            )

            # Track uploaded files for reference
            for i, path in enumerate(valid_paths):
                self.uploaded_files.append(
                    UploadedFile(
                        original_path=str(path),
                        file_id=file_ids[i],
                        file_name=path.name,
                    )
                )
                logfire.info(f"Uploaded: {path.name} (ID: {file_ids[i]})")

            return file_ids
        else:
            logfire.info("No valid files to upload")
            return []

    async def generate_docx_report(
        self, validation_result: CompliantModel, report_title: str = "Compliance Report"
    ) -> ReportGenerationResult:
        """
        Step 3: Generate a DOCX report using the existing validation result
        """
        if not self.container:
            raise Exception("Container not created. Call create_container() first.")

        # Prepare the prompt for report generation using existing validation result
        evidence_summary = "\n".join(
            [f"- {file.file_name}" for file in self.uploaded_files]
        )

        prompt = f"""
You are a professional report generator. Create a comprehensive DOCX report based on the existing compliance validation analysis.

REPORT TITLE: {report_title}

EXISTING COMPLIANCE ANALYSIS:
- Compliance Status: {validation_result.answer}
- Reasoning: {validation_result.reasoning}
- Compliant Evidence: {', '.join(validation_result.compliant_evidence) if validation_result.compliant_evidence else 'None'}
- Non-Compliant Evidence: {', '.join(validation_result.non_compliant_evidence) if validation_result.non_compliant_evidence else 'None'}

EVIDENCE FILES AVAILABLE:
{evidence_summary}

Please create a professional DOCX report that includes:
1. Executive Summary (based on the compliance status)
2. Detailed Analysis (using the existing reasoning)
3. Key Findings (from the compliance validation)
4. Recommendations (if applicable)
5. Appendices with relevant evidence

The report should be well-structured, professional, and comprehensive, building upon the existing compliance analysis rather than re-analyzing the evidence.
Then you just return the file name of the report, no other text.
"""

        try:
            # Generate the report using the container
            resp = await create_response_with_container(
                self.client, self.container.id, prompt, model=MODEL_NAME
            )
            if resp.status == "completed":
                response_text = resp.output_text
            else:
                raise Exception(f"Response status: {resp.status}")

            # Return container and file information
            return ReportGenerationResult(
                container_id=self.container.id,
                report_generated=True,
                response_text=response_text,
                uploaded_files=self.uploaded_files,
            )

        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}")

    async def generate_report_with_evidence(
        self,
        validation_result: CompliantModel,
        report_title: str = "Compliance Report",
    ) -> ReportGenerationResult:
        """
        Complete workflow: Create container, upload evidence, and generate report using existing validation
        """
        try:
            evidence_files = (
                validation_result.compliant_evidence
                + validation_result.non_compliant_evidence
            )
            # Step 1: Create container
            container_id = await self.create_container()
            logfire.info(f"Container created: {container_id}")

            # Step 2: Upload evidence
            if len(evidence_files) > 0:
                file_ids = await self.upload_evidence(evidence_files)
                logfire.info(f"Uploaded {len(file_ids)} files")
            else:
                logfire.info("No evidence files to upload")

            # Step 3: Generate report using existing validation result
            result = await self.generate_docx_report(validation_result, report_title)

            return result

        except Exception as e:
            raise Exception(f"Report generation failed: {str(e)}")

    async def cleanup(self):
        """
        Clean up the container (optional - containers may have automatic cleanup)
        """
        if self.container:
            try:
                await delete_container(self.client, self.container.id)
                logfire.info(f"Container {self.container.id} cleanup completed")
            except Exception as e:
                logfire.warning(f"Cleanup warning: {str(e)}")

    async def list_container_files(self, container_id: str) -> List[ContainerFile]:
        """
        List all files in a container
        """
        try:
            files = await list_container_files(self.client, container_id)
            return [ContainerFile(**file) for file in files]
        except Exception as e:
            raise Exception(f"Failed to list container files: {str(e)}")

    async def find_report_file(
        self, container_id: str, report_filename: str
    ) -> Optional[ContainerFile]:
        """
        Find a specific file in the container by filename
        """
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
        """
        Download a file from the container
        """
        try:

            # Download the file
            downloaded_path = await download_specific_file(
                self.client, container_id, file_id, output_path
            )
            return downloaded_path

        except Exception as e:
            raise Exception(f"Failed to download report: {str(e)}")

    async def download_generated_report(
        self, container_id: str, report_filename: str, output_path: str
    ) -> str:
        """
        Complete workflow to find and download the generated report
        """
        try:
            # Find the report file
            report_file = await self.find_report_file(container_id, report_filename)
            if not report_file:
                raise Exception(
                    f"Report file '{report_filename}' not found in container"
                )

            # Download the report
            downloaded_path = await self.download_report(
                container_id, report_file.id, Path(output_path) / report_filename
            )
            return downloaded_path

        except Exception as e:
            raise Exception(f"Failed to download generated report: {str(e)}")
