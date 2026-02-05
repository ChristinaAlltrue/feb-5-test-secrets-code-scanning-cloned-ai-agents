import ipaddress
import os
import pathlib
from io import BytesIO
from typing import List
from urllib.parse import urlparse
from uuid import uuid4

import logfire
import pandas as pd
from alltrue.agents.schema.action_execution import PlainTextLog
from httpx import HTTPStatusError
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.mcp import MCPServerStdio

from app.core.agents.action_prototype.custom_questionnaire_assistant_v2.prompt import (
    CUSTOM_QUESTIONNAIRE_ASSISTANT_V2_PROMPT,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant_v2.schema import (
    CustomQuestionnaireAssistantV2AgentDeps,
    CustomQuestionnaireAssistantV2Output,
    LocalFileSaveResult,
    ProcessingResult,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json


class UpdateCellsInput(BaseModel):
    column_index: int = Field(
        ...,
        description="Column index (1-based) to update. Use 1 for first column, 2 for second column, etc.",
    )
    values: List[str] = Field(
        ...,
        description="List of values to insert into the column. These will be inserted starting from start_row_position.",
    )
    start_row_position: int = Field(
        default=1,
        description="Starting row position (1-based index) where values should be inserted. Default is 1 (first row).",
    )


class AddColumnInput(BaseModel):
    values: List[str] = Field(
        ...,
        description="List of values for the new column. MUST contain exactly the same number of values as rows in the DataFrame, in the same order as the rows appear.",
    )
    column_position: int | None = Field(
        default=None,
        description="Position to insert the new column (1-based index). If None, column will be appended at the end.",
    )


def validate_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    host = parsed.hostname or ""
    # Block localhost and literal private addresses
    if host in {"localhost"}:
        raise ValueError("Localhost is not allowed")
    try:
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise ValueError("Private or local IPs are not allowed")
    except ValueError:
        # Not an IP literal; consider DNS allowlisting or egress firewall for full protection.
        pass


def _resolve_and_guard_path(path: str, working_dir: str) -> pathlib.Path:
    p = pathlib.Path(path).expanduser().resolve()
    wd = pathlib.Path(working_dir).expanduser().resolve()
    try:
        p.relative_to(wd)
    except ValueError:
        raise ModelRetry(f"File path '{path}' is outside the working directory")
    if not p.exists():
        raise ModelRetry(f"File '{path}' does not exist")
    return p


async def read_excel_file(
    ctx: RunContext[CustomQuestionnaireAssistantV2AgentDeps],
    downloaded_sheet_file_path: str,
) -> str:
    """
    Read the excel file and return the content and import the content into the context
    """
    try:
        safe_path = _resolve_and_guard_path(
            downloaded_sheet_file_path, ctx.deps.working_dir
        )
        df = pd.read_excel(str(safe_path), engine="openpyxl", header=None)
        df.columns = [f"Column {i+1}" for i in range(len(df.columns))]
        df_display = df.copy()
        df_display.index = range(1, len(df) + 1)

        readable_content = f"Excel file content (with 1-based row and column indices):\n{df_display.to_string(index=True)}"
        ctx.deps.original_dataframe = df
        logfire.info(f"Original dataframe: {df.head(5)}")
        return readable_content

    except Exception as e:
        logfire.error(f"Failed to read Excel file: {e}")
        raise ModelRetry(f"Retryable Excel read error: {e}")


async def read_context_document(
    ctx: RunContext[CustomQuestionnaireAssistantV2AgentDeps],
    downloaded_context_document_file_path: str,
) -> str:
    """
    Read the context document and return the content and import the content into the context.
    """
    try:
        safe_path = _resolve_and_guard_path(
            downloaded_context_document_file_path, ctx.deps.working_dir
        )
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        ctx.deps.context_content = content
        return content

    except Exception as e:
        logfire.error(f"Failed to read context document: {e}")
        raise ModelRetry(f"Retryable context document read error: {e}")


def save_file_to_local(
    content: str | bytes, file_name: str, working_dir: str
) -> LocalFileSaveResult:
    """Save file content to local directory and return the file info.

    Args:
        content: File content as string or bytes
        file_name: Name of the file to save
        working_dir: Directory to save the file in

    Returns:
        LocalFileSaveResult with file name and path
    """
    file_path = f"{working_dir}/{file_name}"

    if isinstance(content, str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        with open(file_path, "wb") as f:
            f.write(content)

    return LocalFileSaveResult(file_name=file_name, file_path=file_path)


def _validate_dataframe_exists(df: pd.DataFrame | None) -> None:
    """Validate that DataFrame exists in context."""
    if df is None:
        raise ModelRetry(
            "No spreadsheet data was found in context. Before you modify the spreadsheet, please ensure the spreadsheet was properly read after you export it."
        )


def _validate_column_index(column_index: int, df: pd.DataFrame) -> None:
    """Validate column index is within bounds (1-based)."""
    if column_index < 1 or column_index > len(df.columns):
        raise ModelRetry(
            f"Column index {column_index} is invalid. Valid column indices are 1 to {len(df.columns)}. "
            f"The spreadsheet has {len(df.columns)} columns."
        )


def _validate_row_capacity(start_row: int, values_count: int, df: pd.DataFrame) -> None:
    """Validate that values can fit in the DataFrame starting from start_row."""
    if start_row < 1:
        raise ModelRetry(f"start_row_position must be at least 1, got {start_row}")

    end_row_idx = (start_row - 1) + values_count
    if end_row_idx > len(df):
        raise ModelRetry(
            f"Cannot insert {values_count} values starting at row {start_row}. "
            f"This would exceed the spreadsheet which has {len(df)} rows. "
            f"Please provide fewer values or start from an earlier row position."
        )


def _validate_values_match_rows(values: List[str], df: pd.DataFrame) -> None:
    """Validate that values count matches DataFrame row count."""
    if len(values) != len(df):
        raise ModelRetry(
            f"The number of column values ({len(values)}) does not match the number of rows in the spreadsheet ({len(df)}). "
            f"You must provide exactly one value for each row. Please analyze the spreadsheet content again and provide {len(df)} values in the values list."
        )


def _validate_column_position(column_position: int | None, df: pd.DataFrame) -> None:
    """Validate column position is within valid bounds (1-based)."""
    if column_position is not None:
        max_position = df.shape[1] + 1  # Can insert after the last column
        if column_position < 1 or column_position > max_position:
            raise ModelRetry(
                f"Column position {column_position} is invalid. "
                f"Valid column positions are 1 to {max_position} (1-based). "
                f"The spreadsheet has {df.shape[1]} columns."
            )


def save_excel_and_context(
    df: pd.DataFrame,
    context_content: str,
    working_dir: str,
    excel_prefix: str = "processed_sheet",
) -> tuple[LocalFileSaveResult, LocalFileSaveResult]:
    """Save Excel dataframe and context document, return both results.

    Args:
        df: DataFrame to save as Excel
        context_content: Context document content
        working_dir: Directory to save files in
        excel_prefix: Prefix for Excel filename

    Returns:
        Tuple of (excel_result, context_result)
    """
    # Save Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, header=False)
    excel_bytes = excel_buffer.getvalue()
    excel_file_name = f"{excel_prefix}_{uuid4().hex[:8]}.xlsx"
    excel_result = save_file_to_local(excel_bytes, excel_file_name, working_dir)

    # Save context document
    context_file_name = f"context_document_{uuid4().hex[:8]}.txt"
    context_result = save_file_to_local(context_content, context_file_name, working_dir)

    return excel_result, context_result


async def update_existing_cells(
    ctx: RunContext[CustomQuestionnaireAssistantV2AgentDeps],
    input_data: UpdateCellsInput,
) -> ProcessingResult:
    """Update values in existing cells of the spreadsheet.

    This tool is for updating existing columns with new values. Use this when you want to
    fill in empty cells or update existing values in columns that already exist.

    Args:
        ctx: RunContext containing original DataFrame in context
        input_data: UpdateCellsInput containing column name and list of (row, value) updates

    Returns:
        ProcessingResult with updated spreadsheet and context document
    """
    try:
        # Get original DataFrame from context
        df = ctx.deps.original_dataframe
        _validate_dataframe_exists(df)
        _validate_column_index(input_data.column_index, df)
        _validate_row_capacity(
            input_data.start_row_position, len(input_data.values), df
        )

        # Get the actual column name from the index
        column_name = df.columns[
            input_data.column_index - 1
        ]  # Convert to 0-based index

        # Log agent's decision-making
        logfire.info(
            f"Agent decision: updating column {input_data.column_index} ('{column_name}') with {len(input_data.values)} values starting from row {input_data.start_row_position}"
        )
        logfire.info(f"Agent values: {input_data.values}")

        # Convert to 0-based index for pandas operations
        start_row_idx = input_data.start_row_position - 1

        # Apply updates to consecutive rows
        updates_applied = 0
        for i, value in enumerate(input_data.values):
            row_idx = start_row_idx + i
            df.at[row_idx, column_name] = value
            updates_applied += 1

        # Save Excel and context files
        excel_result, context_result = save_excel_and_context(
            df, ctx.deps.context_content, ctx.deps.working_dir, "updated_sheet"
        )

        logfire.info(
            f"Updated {updates_applied} cells in column {input_data.column_index} ('{column_name}') starting from row {input_data.start_row_position}"
        )

        # Return structured result
        return ProcessingResult(
            modified_spreadsheet=excel_result,
            context_document=context_result,
            questions_answered=updates_applied,
            total_rows=len(df),
        )

    except Exception as e:
        logfire.error(f"Failed to update Excel cells: {e}")
        raise


async def add_new_column(
    ctx: RunContext[CustomQuestionnaireAssistantV2AgentDeps], input_data: AddColumnInput
) -> ProcessingResult:
    """Add a new column to the Excel file with specified values.

    This tool is for creating entirely new columns. Use this when you need to add
    a column that doesn't exist in the original spreadsheet.

    Args:
        ctx: RunContext containing original DataFrame in context
        input_data: AddColumnInput containing column name, values, and positions

    Returns:
        ProcessingResult with modified spreadsheet and context document
    """
    try:
        # Get original DataFrame from context
        df = ctx.deps.original_dataframe
        _validate_dataframe_exists(df)
        _validate_values_match_rows(input_data.values, df)
        _validate_column_position(input_data.column_position, df)

        # Generate column name automatically
        column_name = f"Column {len(df.columns) + 1}"

        # Log agent's decision-making
        logfire.info(
            f"Agent decision: adding new column '{column_name}' at position {input_data.column_position}, values_count={len(input_data.values)}"
        )
        logfire.info(f"Agent values: {input_data.values}")

        # Add new column with specified name and values at the specified position
        if input_data.column_position is not None:

            # Convert 1-based position to 0-based for pandas
            pandas_position = input_data.column_position - 1
            # Insert column at specific position
            df.insert(pandas_position, column_name, input_data.values)
        else:
            # Append column at the end
            df[column_name] = input_data.values

        # Save Excel and context files
        excel_result, context_result = save_excel_and_context(
            df, ctx.deps.context_content, ctx.deps.working_dir, "modified_sheet"
        )

        # Create summary of filled values
        values_filled = len(input_data.values)
        total_rows = len(df)

        column_position_info = (
            f" at column position {input_data.column_position}"
            if input_data.column_position is not None
            else " at the end"
        )
        logfire.info(
            f"Modified Excel file with column '{column_name}' containing {values_filled} values{column_position_info}"
        )

        # Return structured result
        return ProcessingResult(
            modified_spreadsheet=excel_result,
            context_document=context_result,
            questions_answered=values_filled,
            total_rows=total_rows,
        )

    except Exception as e:
        logfire.error(f"Failed to modify Excel file: {e}")
        raise


async def custom_questionnaire_assistant_v2(
    ctx: RunContext[ActionDeps],
    google_token: str,
    sheet_name: str,
    context_document_name: str,
    goal: str,
) -> CustomQuestionnaireAssistantV2Output:

    try:
        refreshed_credentials_json = get_refreshed_credentials_json(google_token)
        google_drive_mcp_server = MCPServerStdio(
            command="uv",
            args=["run", "python", "-m", "mcp_server.google_drive.server"],
            env={
                "GOOGLE_CREDENTIALS": refreshed_credentials_json,
                "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
                "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
                "WORKING_DIR": str(pathlib.Path(f"{ctx.deps.working_dir}").resolve()),
            },
        )
        QUESTIONNAIRE_ASSISTANT_AGENT = Agent(
            model=get_pydanticai_openai_llm(),
            deps_type=CustomQuestionnaireAssistantV2AgentDeps,
            output_type=CustomQuestionnaireAssistantV2Output,
            system_prompt=CUSTOM_QUESTIONNAIRE_ASSISTANT_V2_PROMPT,
            toolsets=[google_drive_mcp_server],
            tools=[
                Tool(read_excel_file, takes_ctx=True, max_retries=5),
                Tool(read_context_document, takes_ctx=True, max_retries=5),
                Tool(update_existing_cells, takes_ctx=True, max_retries=5),
                Tool(add_new_column, takes_ctx=True, max_retries=5),
            ],
        )

        # Create deps for the agent with original DataFrame and context content
        deps: CustomQuestionnaireAssistantV2AgentDeps = ctx.deps.model_copy(
            update={
                "sheet_name": sheet_name,
                "context_document_name": context_document_name,
                "goal": goal,
                "original_dataframe": None,
                "context_content": "",
            }
        )
        try:
            result = await QUESTIONNAIRE_ASSISTANT_AGENT.run(
                f"""
                1. There is a sheet on the google drive called {sheet_name}, you have to export it to a xlsx file.
                2. There is a context document on the google drive called {context_document_name}, you have to export it to a txt file.
                3. After exporting the files, you have to read the sheet and the context document to import the content into the dependencies.
                4. Then, you have to use update_existing_cells or add_new_column to answer the questions in the spreadsheet based on the context document.
                Goal: {goal}
                """,
                deps=deps,  # Available for future tool access if needed (currently not used)
            )
        except* HTTPStatusError as eg:
            for err in eg.exceptions:  # type: HTTPStatusError
                await ctx.deps.add_log(
                    PlainTextLog(
                        data=f"Unable to access Google Drive server: Status code: {err.response.status_code}"
                    )
                )
            logfire.error(f"CustomQuestionnaireAssistantV2Agent failed: {eg}")
            raise Exception("Unable to access google drive server")

        await ctx.deps.add_log(
            PlainTextLog(data="Successfully completed spreadsheet processing")
        )

        return result.output

    except Exception as e:
        await ctx.deps.add_log(PlainTextLog(data=f"Error: {str(e)}"))
        logfire.error(f"CustomQuestionnaireAssistant failed: {e}")
        raise
