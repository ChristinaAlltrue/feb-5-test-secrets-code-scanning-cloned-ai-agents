import hashlib
import traceback
import uuid
from pathlib import Path
from typing import List, Optional

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic import BaseModel, Field
from pydantic_ai import ModelRetry, RunContext

from app.core.agents.action_prototype.supervisor_agent.tools import (
    get_file_list_in_control_execution_dir,
)
from app.core.agents.utils.openai_utils.response_with_tool_code_interpreter import (
    CodeInterpreterResponseManager,
)
from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.llm.model_registry import ModelRegistry

MODEL_NAME = "gpt-5"


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file for comparison."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class AuditAnalysisAgentSimpleOutput(BaseModel):
    successful: bool = Field(
        description="Whether the container agent executed successfully",
    )
    feedback: str = Field(
        description="The response from the container agent",
    )
    generated_files: Optional[List[str]] = Field(
        description="The file path of the generated report file",
        default=None,
    )


async def advanced_data_analysis_tool(
    ctx: RunContext[ToolActionDeps],
    task: str,
    file_paths: list[str],
):
    """
    This tool is used to analyze and generate output files based on the given task and files in the working directory.
    - if you are going to process the files, you may need to call the tool `list_working_directory_files` first to make sure the file you are going to process actually exists in the working directory.

    Args:
        task: The task to be performed.
        file_paths: The path of the files in the working directory that the task needs to process.

    """
    await ctx.deps.add_log(
        PlainTextLog(data="Starting Advanced Data Analysis Tool"),
    )
    logfire.info(f"Task: {task}")
    files_to_upload: List[Path] = []
    action_working_dir = ctx.deps.action_working_dir
    working_directory_files = get_file_list_in_control_execution_dir(
        ctx.deps.working_dir
    )
    logfire.info(
        f"Target files: {file_paths}. Current files in the working directory: {working_directory_files}"
    )

    for target_file_path in file_paths:
        resolved_path = Path(target_file_path).resolve()

        # check if the resolved path exists in the working directory
        if resolved_path in working_directory_files:
            files_to_upload.append(resolved_path)
        else:
            raise ModelRetry(
                f"File {target_file_path} does not exist. The current files in the working directory are: {working_directory_files}"
            )

    try:
        container_name = str(
            f"{ctx.deps.control_info.control_execution_id}{uuid.uuid4().hex[:6]}"
        )
        selected_model = ModelRegistry.MODELS.get(ctx.deps.selected_model)
        if not selected_model:
            selected_model_id = MODEL_NAME
        else:
            selected_model_id = selected_model["model_id"]

        async with CodeInterpreterResponseManager(
            container_name, selected_model_id
        ) as manager:
            await ctx.deps.add_log(
                PlainTextLog(data="Setting up sandbox environment"),
            )

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
            }
            valid_files = []
            for p in files_to_upload:
                if p.is_file() and p.exists():
                    if p.suffix in target_type:
                        valid_files.append(p)
                    else:
                        logfire.error(f"File {p} has unsupported format: {p.suffix}")
                else:
                    logfire.error(f"File {p} does not exist")

            # Upload files and map IDs to their original hashes
            uploaded_file_ids = await manager.upload_files(valid_files)

            # Create mapping of file_id -> original hash (assumes order is preserved)
            uploaded_file_hashes = {
                file_id: compute_file_hash(file_path)
                for file_id, file_path in zip(uploaded_file_ids, valid_files)
            }
            logfire.info(
                f"Computed hashes for {len(uploaded_file_hashes)} uploaded files"
            )

            # Step 3: Run the main agent
            await ctx.deps.add_log(
                PlainTextLog(data="Running advanced data analysis"),
            )
            response = await manager.execute_code(
                task,
                save_output_to=Path(f"{action_working_dir}/response_output.json"),
            )

            if response.status == "completed":
                response_text = response.output_text
            else:
                raise Exception(f"Response status: {response.status}")

            await ctx.deps.add_log(
                PlainTextLog(data=f"Advanced data analysis result: {response_text}"),
            )

            # Step 4: Download all files and compare with uploaded files by ID
            container_files = await manager.list_files()
            logfire.info(f"Number of files in container: {len(container_files)}")
            downloaded_files = []
            for file in container_files:
                container_file_id = file["id"]
                container_file_name = file["name"]
                logfire.info(f"Found file in container: {container_file_name}")

                # Download the file first
                if not ctx.deps.working_dir:
                    raise RuntimeError("Working directory not available")

                logfire.info(
                    f"Downloading file: {container_file_name} (ID: {container_file_id})"
                )
                report_file_path = await manager.download_file(
                    filename=container_file_name,
                    destination_dir=action_working_dir,
                    file_id=container_file_id,
                )

                if report_file_path is None:
                    logfire.warning(f"Failed to download file: {container_file_name}")
                    continue

                # Compare with uploaded file by ID if it was uploaded
                if container_file_id in uploaded_file_hashes:
                    downloaded_hash = compute_file_hash(Path(report_file_path))
                    original_hash = uploaded_file_hashes[container_file_id]

                    if downloaded_hash == original_hash:
                        logfire.info(
                            f"File '{container_file_name}' (ID: {container_file_id}) was not modified - skipping"
                        )
                        # Remove the unmodified file
                        Path(report_file_path).unlink()
                        continue
                    else:
                        logfire.info(
                            f"File '{container_file_name}' (ID: {container_file_id}) was modified - including in results"
                        )
                else:
                    logfire.info(
                        f"File '{container_file_name}' (ID: {container_file_id}) is a new output file - including in results"
                    )

                downloaded_files.append(report_file_path)

            # Container cleanup is handled automatically by the context manager
            if manager.container_id:
                await ctx.deps.add_log(
                    PlainTextLog(
                        data=f"Sandbox environment {manager.container_id} will be cleaned up automatically"
                    ),
                )

        if downloaded_files:
            result = AuditAnalysisAgentSimpleOutput(
                successful=True,
                feedback=response_text,
                generated_files=downloaded_files,
            )
        else:
            result = AuditAnalysisAgentSimpleOutput(
                successful=False,
                feedback=response_text,
                generated_files=None,
            )

        await ctx.deps.add_log(
            [
                PlainTextLog(data="Advanced data analysis agent workflow completed"),
                ObjectLog(data=result.model_dump()),
            ]
        )

        logfire.info(f"Advanced data analysis agent completed: {result}")
        return result

    except Exception as e:
        logfire.trace(f"Advanced data analysis agent failed: {e}")
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Advanced data analysis agent workflow failed"),
                ObjectLog(data={"error": str(e)}),
            ]
        )
        traceback.print_exc()
        raise
