import asyncio
import json
import os
import pathlib

import logfire
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.utils.logfire import set_logfire_token_env_variables
from test_suite.credential import GOOGLE_CREDENTIALS

set_logfire_token_env_variables()
logfire.configure()
logfire.instrument_pydantic_ai()


async def example_list_files(session):
    print("=== List Files Example ===")
    params = {
        "query": "mimeType != 'application/vnd.google-apps.folder'",
        "page_size": 5,
    }
    result = await session.call_tool("list_files", params)
    print(result.content)


def _extract_content_dict(result) -> dict:
    """Normalize MCP result.content into a dict.

    - If content is a list with a TextContent element, parse its .text as JSON
    - If content is already a dict, return it directly
    - If content is a list with a dict, return the first dict
    - Otherwise return an empty dict
    """
    content = result.content
    if isinstance(content, dict):
        return content
    if isinstance(content, list) and content:
        first = content[0]
        text = getattr(first, "text", None)
        if isinstance(text, str):
            try:
                return json.loads(text)
            except Exception:
                return {}
        if isinstance(first, dict):
            return first
    return {}


async def example_download_file(session, file_id: str):
    print("\n=== Download File Example ===")
    result = await session.call_tool("download_file", {"file_id": file_id})
    data = _extract_content_dict(result)
    print({k: v for k, v in data.items()})
    if data.get("saved_path"):
        print(f"File saved at: {data['saved_path']}")


async def example_export_doc(session, file_id: str):
    print("\n=== Export Document Example (pdf) ===")
    result = await session.call_tool(
        "export_document", {"file_id": file_id, "format": "pdf"}
    )
    data = _extract_content_dict(result)
    print({k: v for k, v in data.items()})
    if data.get("saved_path"):
        print(f"File saved at: {data['saved_path']}")


async def example_export_sheet(session, file_id: str):
    print("\n=== Export Spreadsheet Example (xlsx) ===")
    result = await session.call_tool(
        "export_spreadsheet", {"file_id": file_id, "format": "xlsx"}
    )
    data = _extract_content_dict(result)
    print({k: v for k, v in data.items()})
    if data.get("saved_path"):
        print(f"File saved at: {data['saved_path']}")


async def main():
    print("Google Drive MCP Server Examples")
    print("=" * 50)

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "mcp_server.google_drive.server"],
        env={
            "GOOGLE_CREDENTIALS": GOOGLE_CREDENTIALS,
            "WORKING_DIR": str(
                pathlib.Path("UserData/GoogleDriveMCPExamples").resolve()
            ),
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
    )

    output_dir = "UserData/GoogleDriveMCPExamples"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await example_list_files(session)
            # Fill in real file ids to try the examples below
            # After server change, responses contain saved_path; files are saved directly in WORKING_DIR.
            # await example_download_file(session, file_id="<file_id>")
            # await example_export_doc(session, file_id="<doc_file_id>")
            # await example_export_sheet(session, file_id="<sheet_file_id>")


if __name__ == "__main__":
    asyncio.run(main())
