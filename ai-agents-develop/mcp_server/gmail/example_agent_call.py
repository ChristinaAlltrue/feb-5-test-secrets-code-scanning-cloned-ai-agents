import asyncio
import os

import logfire
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from app.utils.logfire import set_logfire_token_env_variables
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json
from test_suite.credential import GOOGLE_CREDENTIALS

set_logfire_token_env_variables()
logfire.configure()
logfire.instrument_pydantic_ai()


async def client():
    refreshed_credentials_json = get_refreshed_credentials_json(GOOGLE_CREDENTIALS)
    server = MCPServerStdio(
        command="uv",
        args=["run", "python", "-m", "mcp_server.gmail.server"],
        env={
            "GOOGLE_CREDENTIALS": refreshed_credentials_json,
            "LOGFIRE_TOKEN": os.environ["LOGFIRE_TOKEN"],
            "LOGFIRE_SERVICE_NAME": os.environ["LOGFIRE_SERVICE_NAME"],
        },
    )

    agent = Agent(model=get_pydanticai_openai_llm(), toolsets=[server])
    result = await agent.run(
        "Check is there any email about Task 001, if there is, show me the content of the email"
    )
    print(result.output)


if __name__ == "__main__":
    asyncio.run(client())
