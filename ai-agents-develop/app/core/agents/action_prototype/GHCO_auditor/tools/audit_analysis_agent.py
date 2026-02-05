import traceback
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, Tool

from app.core.agents.utils.openai_utils.response_with_tool_code_interpreter import (
    CodeInterpreterResponseManager,
)
from app.core.graph.deps.action_deps import ActionDeps

MODEL_NAME = "gpt-5"


class AuditAnalysisAgentSimpleOutput(BaseModel):
    successful: bool = Field(
        description="Whether the container agent executed successfully",
    )
    feedback: str = Field(
        description="The response from the container agent",
    )
    generated_file: Optional[str] = Field(
        description="The file path of the generated report file",
        default=None,
    )


def ensure_newlines(text: str) -> str:
    if text:
        if not text.startswith("\n"):
            text = "\n" + text
        if not text.endswith("\n"):
            text += "\n"
        return text
    return text


class TARGET_OUTPUT(Enum):
    USER_LIST = "user_list"
    PROVISIONING = "provisioning"


async def audit_analysis_agent(
    ctx: RunContext[ActionDeps],
    report_instructions: str,
    software_list: List[str],
    files_to_upload: Optional[List[str]] = None,
    target_output: TARGET_OUTPUT = TARGET_OUTPUT.USER_LIST,
    save_output_to: Optional[
        Path
    ] = None,  # Path("test_suite/sample_files/GAM/response_output.json")
) -> AuditAnalysisAgentSimpleOutput:
    """
    This tool runs a comprehensive audit analysis workflow to process multiple file formats and generate audit reports.

    Args:
        report_instructions: Instructions for the audit analysis agent, should include audit requirements and report generation rules
        software_list: List of softwares to analyze
        files_to_upload: List of file paths to upload (supports Excel, PDF, images, text, logs, etc.)
    """

    await ctx.deps.add_log(
        PlainTextLog(data="Starting audit analysis agent"),
    )
    logfire.info(f"Audit analysis agent started: {software_list}, {files_to_upload}")

    # validate the input
    if not files_to_upload:  #  or not software_list
        return AuditAnalysisAgentSimpleOutput(
            successful=False,
            feedback="No files to upload or softwares to analyze",
            generated_file=None,
        )

    try:
        container_name = str(ctx.deps.control_info.control_execution_id)

        # Use the new CodeInterpreterManager
        async with CodeInterpreterResponseManager(
            container_name, MODEL_NAME
        ) as manager:
            await ctx.deps.add_log(
                PlainTextLog(data="Setting up sandbox environment"),
            )

            if target_output == TARGET_OUTPUT.USER_LIST:
                TEMPLATE_FILES = [
                    "app/core/agents/action_prototype/GHCO_auditor/tools/scripts_template/AC2_New_user_Sample_for_Business_Unit.xlsx",
                ]
            elif target_output == TARGET_OUTPUT.PROVISIONING:
                TEMPLATE_FILES = [
                    "app/core/agents/action_prototype/GHCO_auditor/tools/scripts_template/Detailed Testing Table - Access Provisioning.xlsx"
                ]

            # Upload files
            merged_files_to_upload = TEMPLATE_FILES + files_to_upload
            await ctx.deps.add_log(
                PlainTextLog(data=f"Uploading {len(files_to_upload)} files..."),
            )

            # Filter supported file types
            target_type = {
                ".csv",
                ".xlsx",
                ".xls",
                ".py",
                ".pdf",
                ".txt",
                ".png",
                ".jpg",
                ".jpeg",
                ".docx",
                ".log",
                ".zip",
                "",  # for files without extension
            }
            valid_files = []
            for file_path in merged_files_to_upload:
                p = Path(file_path)
                if p.is_file() and p.exists():
                    if p.suffix in target_type:
                        valid_files.append(str(p))
                    else:
                        logfire.error(f"File {p} has unsupported format: {p.suffix}")
                else:
                    logfire.error(f"File {p} does not exist")

            await manager.upload_files(valid_files)

            # Step 3: Run the main agent
            await ctx.deps.add_log(
                PlainTextLog(data="Running audit analysis"),
            )
            report_name = "output.xlsx"

            # Build the complete prompt with system instructions
            prompt = f"""
You are an intelligent IT Audit Analysis Agent. Analyze all the uploaded files and perform appropriate audit testing. Based on the output excel template columns, extract required information and fill the excel.

SOFTWARES: {software_list}

TECHNICAL GUIDANCE:
- Use your own visual capability for images, do not rely on OCR since it may be inaccurate and the spacial information will be lost easily
- Use your own visual capability for PDFs since the layout is important, get text from PDF only when image is too blur
- Only write code for complex analysis, otherwise, just get the text and output your answers to the output file. Do not use code to extract information since there would be too many edge cases
- You must ensure that all fields are filled
{ensure_newlines(dedent(report_instructions))}
DELIVERABLES:
- Your final output Excel file should be edited from the template Excel file, since it has the correct formatting
- Make sure to keep the column name and the formatting of all the cells as appropriate
- Be careful that there may be multiple header rows
- Separate any working tables with the final output file, strictly follow the template file, do not add new sheets to the final output file
- Copy the style of the sample rows to all the new rows
- The final output should be saved as {report_name}
"""

            # # Save prompt to a file for debug
            # with open(
            #     "test_suite/sample_files/GAM/audit_assistant_agent_prompt.txt", "w"
            # ) as f:
            #     f.write(prompt)

            # Execute the analysis
            response = await manager.execute_code(
                prompt,
                save_output_to=save_output_to,
            )

            if response.status == "completed":
                response_text = response.output_text
            else:
                raise Exception(f"Response status: {response.status}")

            await ctx.deps.add_log(
                PlainTextLog(data=f"Audit analysis result: {response_text}"),
            )

            # Step 4: Download the report file
            container_files = await manager.list_files()
            report_file_found = False

            for file in container_files:
                logfire.info(f"Found file in container: {file['name']} ({file['id']})")
                if file["name"] == report_name:
                    report_file_found = True
                    break
                # May download other files as evidence

            if report_file_found:
                logfire.info(f"Downloading report file: {report_name}")
                if not ctx.deps.working_dir:
                    raise RuntimeError("Working directory not available")
                report_file_path = await manager.download_file(
                    report_name,
                    ctx.deps.working_dir,
                )
            else:
                logfire.error("No report file found", data={"response": str(response)})
                report_file_path = None

            # Container cleanup is handled automatically by the context manager
            if manager.container_id:
                await ctx.deps.add_log(
                    PlainTextLog(
                        data=f"Sandbox environment {manager.container_id} will be cleaned up automatically"
                    ),
                )

        if report_file_path:
            result = AuditAnalysisAgentSimpleOutput(
                successful=True,
                feedback=response_text,
                generated_file=report_file_path,
            )
        else:
            result = AuditAnalysisAgentSimpleOutput(
                successful=False,
                feedback=response_text,
                generated_file=None,
            )

        await ctx.deps.add_log(
            [
                PlainTextLog(data="Audit analysis agent workflow completed"),
                ObjectLog(data=result.model_dump()),
            ]
        )

        logfire.info(f"Audit analysis agent completed: {result}")
        return result

    except Exception as e:
        logfire.trace(f"Audit analysis agent failed: {e}")
        error_msg = f"Audit analysis agent failed: {e}"
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Audit analysis agent workflow failed"),
                ObjectLog(data={"error": str(e)}),
            ]
        )
        traceback.print_exc()
        raise

        return AuditAnalysisAgentSimpleOutput(
            successful=False,
            feedback=error_msg,
            generated_file=None,
        )


audit_analysis_agent_tool = Tool(audit_analysis_agent, takes_ctx=True)
