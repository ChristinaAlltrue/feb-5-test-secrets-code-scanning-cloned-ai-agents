import asyncio
import os

import logfire
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.utils.logfire import set_logfire_token_env_variables
from test_suite.credential import GOOGLE_CREDENTIALS

set_logfire_token_env_variables()
logfire.configure()
logfire.instrument_pydantic_ai()


async def client():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "mcp_server.gmail.server"],
        env={
            "GOOGLE_CREDENTIALS": GOOGLE_CREDENTIALS,
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(tools)

            result = await session.call_tool("list_mails", {})
            print(result.content)


if __name__ == "__main__":
    asyncio.run(client())
