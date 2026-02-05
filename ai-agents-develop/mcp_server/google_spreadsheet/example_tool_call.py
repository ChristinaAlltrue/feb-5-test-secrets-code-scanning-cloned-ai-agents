"""
Example usage of the Google Spreadsheet MCP Server

This file demonstrates how to use all tools:
1. list_spreadsheets - List available spreadsheets
2. read_spreadsheet_values - Read single range
3. batch_read_spreadsheet_values - Read multiple ranges in batch
4. update_spreadsheet_values - Write to single range
5. batch_update_spreadsheet_values - Write to multiple ranges in batch
6. append_spreadsheet_values - Append data to end of table
"""

import asyncio
import os

import logfire
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.utils.logfire import set_logfire_token_env_variables
from test_suite.credential import GOOGLE_CREDENTIALS, TEST_SPREADSHEET_ID

set_logfire_token_env_variables()
logfire.configure()
logfire.instrument_pydantic_ai()


async def example_list_spreadsheets(session):
    """Example of listing available spreadsheets."""
    print("=== List Spreadsheets Example ===")

    try:
        result = await session.call_tool("list_spreadsheets", {"max_results": 5})
        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error listing spreadsheets: {e}")


async def example_single_range(session):
    """Example of reading a single range from a spreadsheet."""
    print("\n=== Single Range Reading Example ===")

    # Example spreadsheet ID (replace with your actual spreadsheet ID)
    spreadsheet_id = TEST_SPREADSHEET_ID
    range_name = "A1:C5"

    try:
        result = await session.call_tool(
            "read_spreadsheet_values",
            {"spreadsheet_id": spreadsheet_id, "range_name": range_name},
        )

        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error reading single range: {e}")


async def example_batch_ranges(session):
    """Example of reading multiple ranges from a spreadsheet in batch."""
    print("\n=== Batch Range Reading Example ===")

    # Example spreadsheet ID (replace with your actual spreadsheet ID)
    spreadsheet_id = TEST_SPREADSHEET_ID
    range_names = ["A1:C5", "E1:G5", "Sheet1!A1:B3"]

    try:
        result = await session.call_tool(
            "batch_read_spreadsheet_values",
            {"spreadsheet_id": spreadsheet_id, "range_names": range_names},
        )

        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error reading batch ranges: {e}")


async def example_update_single_range(session):
    """Example of updating a single range in a spreadsheet."""
    print("\n=== Single Range Update Example ===")

    # Example spreadsheet ID (replace with your actual spreadsheet ID)
    spreadsheet_id = TEST_SPREADSHEET_ID
    range_name = "A1:C2"
    values = [["Updated A", "Updated B", "Updated C"], ["Row 2", "Data", "Here"]]

    try:
        result = await session.call_tool(
            "update_spreadsheet_values",
            {
                "spreadsheet_id": spreadsheet_id,
                "range_name": range_name,
                "values": values,
                "value_input_option": "USER_ENTERED",
            },
        )

        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error updating single range: {e}")


async def example_batch_update_ranges(session):
    """Example of updating multiple ranges in a spreadsheet using batch operation."""
    print("\n=== Batch Range Update Example ===")

    # Example spreadsheet ID (replace with your actual spreadsheet ID)
    spreadsheet_id = TEST_SPREADSHEET_ID
    updates = [
        {
            "range": "A1:C2",
            "values": [["Batch A", "Batch B", "Batch C"], ["Row 2", "Data", "Here"]],
        },
        {"range": "E1:F2", "values": [["More", "Data"], ["In", "Columns"]]},
    ]

    try:
        result = await session.call_tool(
            "batch_update_spreadsheet_values",
            {
                "spreadsheet_id": spreadsheet_id,
                "updates": updates,
                "value_input_option": "USER_ENTERED",
            },
        )

        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error batch updating ranges: {e}")


async def example_append_values(session):
    """Example of appending values to the end of a table in a spreadsheet."""
    print("\n=== Append Values Example ===")

    # Example spreadsheet ID (replace with your actual spreadsheet ID)
    spreadsheet_id = TEST_SPREADSHEET_ID
    range_name = "A1"  # Append to a1
    values = [["New Row 1", "Passed"], ["New Row 2", "Passed"], ["New Row 3", "Passed"]]

    try:
        result = await session.call_tool(
            "append_spreadsheet_values",
            {
                "spreadsheet_id": spreadsheet_id,
                "range_name": range_name,
                "values": values,
                "value_input_option": "USER_ENTERED",
            },
        )

        print(f"Tool call result: {result.content}")

    except Exception as e:
        print(f"Error appending values: {e}")


async def main():
    """Run all examples using proper MCP client pattern."""
    print("Google Spreadsheet MCP Server Examples")
    print("=" * 50)

    # Note: These examples require proper authentication setup
    # Make sure GOOGLE_CREDENTIALS environment variable is set

    # Set up server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "mcp_server.google_spreadsheet.server"],
        env={
            "GOOGLE_CREDENTIALS": GOOGLE_CREDENTIALS,
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Run all examples
            await example_list_spreadsheets(session)
            await example_single_range(session)
            await example_batch_ranges(session)
            await example_update_single_range(session)
            await example_batch_update_ranges(session)
            await example_append_values(session)

    print("\nExamples completed!")


if __name__ == "__main__":
    # Note: This example requires the server to be properly configured
    # with Google API credentials in the GOOGLE_CREDENTIALS environment variable
    asyncio.run(main())
