import asyncio
import json
import os.path
from typing import Any, Dict, List

import logfire
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

logfire.configure()
logfire.instrument_mcp()

server = FastMCP("Google Spreadsheet MCP Server")


def get_google_service(service_name: str):
    """Get authenticated Google service."""
    logfire.info(f"Getting {service_name} service")
    creds = None

    # Get credentials from environment variable
    token_json_str = os.environ.get("GOOGLE_CREDENTIALS")

    if not token_json_str:
        logfire.error("No valid credentials available")
        raise ConnectionRefusedError("No valid credentials available")

    try:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data)
        logfire.info(f"{service_name} service loaded successfully")
    except Exception as e:
        logfire.error(f"Error loading credentials from token: {e}")
        raise RuntimeError(f"Error loading credentials from token: {e}") from e

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logfire.warning("Access token expired, refreshing...")
            try:
                creds.refresh(Request())
            except RefreshError as e:
                logfire.error(f"Error refreshing credentials: {e}")
                raise ConnectionRefusedError(
                    f"Error refreshing credentials: {e}"
                ) from e
        else:
            logfire.error("No valid credentials available")
            raise ConnectionRefusedError("No valid credentials available")

    logfire.info(f"{service_name} service created successfully")
    return build(
        service_name, "v3" if service_name == "drive" else "v4", credentials=creds
    )


@server.tool()
async def list_spreadsheets(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    List all Google Spreadsheets accessible to the user.

    Args:
        max_results: Maximum number of spreadsheets to return (default: 10)

    Returns:
        List of spreadsheet summaries with id, name, created time, and modified time
    """
    try:
        drive_service = get_google_service("drive")

        # Call the Drive API to list spreadsheets
        response = (
            drive_service.files()
            .list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                pageSize=max_results,
                fields="nextPageToken, files(id, name, createdTime, modifiedTime, owners, size)",
            )
            .execute()
        )

        files = response.get("files", [])

        if not files:
            return []

        spreadsheet_list = []
        for file in files:
            spreadsheet_list.append(
                {
                    "id": file.get("id"),
                    "name": file.get("name"),
                    "created_time": file.get("createdTime"),
                    "modified_time": file.get("modifiedTime"),
                    "owners": [
                        owner.get("displayName", "Unknown")
                        for owner in file.get("owners", [])
                    ],
                    "size": file.get("size", "Unknown"),
                }
            )

        return spreadsheet_list

    except HttpError as error:
        logfire.error(f"An error occurred while listing spreadsheets: {error}")
        return []
    except Exception as e:
        logfire.exception(f"An error occurred while listing spreadsheets: {e}")
        return []


@server.tool()
async def read_spreadsheet_values(
    spreadsheet_id: str, range_name: str = "A1"
) -> Dict[str, Any]:
    """
    Read values from a single range in a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet to read from
        range_name: The range to read (e.g., "A1", "A1:C10", "Sheet1!A1:B5"), "Sheet1!1:1" means the first row of the Sheet1. "Sheet1!A:A" means the first column of the Sheet1.

    Returns:
        Dictionary containing the retrieved values and metadata
    """
    try:
        sheets_service = get_google_service("sheets")

        # Call the Sheets API to get values for a single range
        req = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
        )
        result = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        rows = result.get("values", [])
        row_count = len(rows)

        logfire.info(
            f"{row_count} rows retrieved from spreadsheet {spreadsheet_id}, range {range_name}"
        )

        return {
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "row_count": row_count,
            "values": rows,
            "major_dimension": result.get("majorDimension", "ROWS"),
            "value_range": result.get("valueRange", {}),
        }

    except HttpError as error:
        logfire.error(f"An error occurred while reading spreadsheet: {error}")
        return {
            "error": str(error),
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
        }


@server.tool()
async def batch_read_spreadsheet_values(
    spreadsheet_id: str, range_names: List[str]
) -> Dict[str, Any]:
    """
    Read values from multiple ranges in a Google Spreadsheet using batch operation.

    Args:
        spreadsheet_id: The ID of the spreadsheet to read from
        range_names: List of ranges to read (e.g., ["A1", "B1:D5", "Sheet1!A1:C10"])

    Returns:
        Dictionary containing the retrieved values for all ranges and metadata
    """
    try:
        sheets_service = get_google_service("sheets")

        # Call the Sheets API to get values for multiple ranges
        req = (
            sheets_service.spreadsheets()
            .values()
            .batchGet(spreadsheetId=spreadsheet_id, ranges=range_names)
        )
        result = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        value_ranges = result.get("valueRanges", [])
        total_ranges = len(value_ranges)

        logfire.info(
            f"{total_ranges} ranges retrieved from spreadsheet {spreadsheet_id}"
        )

        # Process each range result
        processed_ranges = []
        for i, value_range in enumerate(value_ranges):
            range_name = value_range.get("range", f"Range_{i}")
            values = value_range.get("values", [])
            row_count = len(values)

            processed_ranges.append(
                {
                    "range": range_name,
                    "row_count": row_count,
                    "values": values,
                    "major_dimension": value_range.get("majorDimension", "ROWS"),
                }
            )

        return {
            "spreadsheet_id": spreadsheet_id,
            "total_ranges": total_ranges,
            "ranges": processed_ranges,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
        }

    except HttpError as error:
        logfire.error(f"An error occurred while batch reading spreadsheet: {error}")
        return {
            "error": str(error),
            "spreadsheet_id": spreadsheet_id,
            "range_names": range_names,
        }


@server.tool()
async def update_spreadsheet_values(
    spreadsheet_id: str,
    range_name: str,
    values: List[List[Any]],
    value_input_option: str = "USER_ENTERED",
) -> Dict[str, Any]:
    """
    Write data to a single range in a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet to write to
        range_name: The range to write to (e.g., "A1", "A1:C10", "Sheet1!A1:B5")
        values: 2D array of values to write (e.g., [["A", "B"], ["C", "D"]])
        value_input_option: How input data should be interpreted ("RAW" or "USER_ENTERED")

    Returns:
        Dictionary containing the update results and metadata
    """
    try:
        sheets_service = get_google_service("sheets")

        # Prepare the request body
        body = {"values": values}

        # Call the Sheets API to update values
        req = (
            sheets_service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
        )
        result = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        updated_cells = result.get("updatedCells", 0)
        updated_range = result.get("updatedRange", range_name)

        logfire.info(f"{updated_cells} cells updated in range {updated_range}")

        return {
            "spreadsheet_id": spreadsheet_id,
            "range": updated_range,
            "updated_cells": updated_cells,
            "updated_rows": result.get("updatedRows", 0),
            "updated_columns": result.get("updatedColumns", 0),
            "value_input_option": value_input_option,
            "result": result,
        }

    except HttpError as error:
        logfire.error(f"An error occurred while updating spreadsheet: {error}")
        return {
            "error": str(error),
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
        }


@server.tool()
async def batch_update_spreadsheet_values(
    spreadsheet_id: str,
    updates: List[Dict[str, Any]],
    value_input_option: str = "USER_ENTERED",
) -> Dict[str, Any]:
    """
    Write data to multiple ranges in a Google Spreadsheet using batch operation.

    Args:
        spreadsheet_id: The ID of the spreadsheet to write to
        updates: List of update objects, each containing "range" and "values"
                (e.g., [{"range": "A1:C2", "values": [["A", "B"], ["C", "D"]]}])
        value_input_option: How input data should be interpreted ("RAW" or "USER_ENTERED")

    Returns:
        Dictionary containing the batch update results and metadata
    """
    try:
        sheets_service = get_google_service("sheets")

        # Prepare the request body for batch update
        body = {"valueInputOption": value_input_option, "data": updates}

        # Call the Sheets API to batch update values
        req = (
            sheets_service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        )
        result = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        total_updated_cells = result.get("totalUpdatedCells", 0)
        total_updated_ranges = result.get("totalUpdatedRanges", 0)

        logfire.info(
            f"{total_updated_cells} cells updated across {total_updated_ranges} ranges"
        )

        # Process individual range results
        responses = result.get("responses", [])
        processed_responses = []

        for response in responses:
            processed_responses.append(
                {
                    "range": response.get("updatedRange", "Unknown"),
                    "updated_cells": response.get("updatedCells", 0),
                    "updated_rows": response.get("updatedRows", 0),
                    "updated_columns": response.get("updatedColumns", 0),
                }
            )

        return {
            "spreadsheet_id": spreadsheet_id,
            "total_updated_cells": total_updated_cells,
            "total_updated_ranges": total_updated_ranges,
            "value_input_option": value_input_option,
            "responses": processed_responses,
            "result": result,
        }

    except HttpError as error:
        logfire.error(f"An error occurred while batch updating spreadsheet: {error}")
        return {
            "error": str(error),
            "spreadsheet_id": spreadsheet_id,
            "updates": updates,
        }


@server.tool()
async def append_spreadsheet_values(
    spreadsheet_id: str,
    range_name: str,
    values: List[List[Any]],
    value_input_option: str = "USER_ENTERED",
) -> Dict[str, Any]:
    """
    Append data to the end of a table in a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet to append to
        range_name: The range to append to (e.g., "A1", "Sheet1!A")
        values: 2D array of values to append (e.g., [["A", "B"], ["C", "D"]])
        value_input_option: How input data should be interpreted ("RAW" or "USER_ENTERED")

    Returns:
        Dictionary containing the append results and metadata
    """
    try:
        sheets_service = get_google_service("sheets")

        # Prepare the request body
        body = {"values": values}

        # Call the Sheets API to append values
        req = (
            sheets_service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
        )
        result = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        updates = result.get("updates", {})
        updated_cells = updates.get("updatedCells", 0)
        updated_range = updates.get("updatedRange", range_name)

        logfire.info(f"{updated_cells} cells appended to range {updated_range}")

        return {
            "spreadsheet_id": spreadsheet_id,
            "range": updated_range,
            "updated_cells": updated_cells,
            "updated_rows": updates.get("updatedRows", 0),
            "updated_columns": updates.get("updatedColumns", 0),
            "value_input_option": value_input_option,
            "table_range": updates.get("tableRange", "Unknown"),
            "result": result,
        }

    except HttpError as error:
        logfire.error(f"An error occurred while appending to spreadsheet: {error}")
        return {
            "error": str(error),
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
        }


if __name__ == "__main__":
    print("Starting the Google Spreadsheet MCP Server")
    server.run()
