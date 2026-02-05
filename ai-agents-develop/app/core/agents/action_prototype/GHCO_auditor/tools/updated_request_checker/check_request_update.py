from pydantic import BaseModel, Field, SecretStr
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.mcp import MCPServerStdio

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm
from mcp_server.utils.google_token_refresh import get_refreshed_credentials_json

from .schema_mixin import GoogleTokenMixin


class CheckRequestUpdateOutput(BaseModel):
    updated_request_ids: list[str] = Field(
        ..., description="The request ids that are updated"
    )


async def check_request_update(
    check_request_ids: list[str], google_credentials: SecretStr
) -> CheckRequestUpdateOutput:
    """
    Determine which of the given request IDs have updates.
    Respond ONLY with a JSON object of shape: {"updated_request_ids": [string]}.
    If none are updated, return {"updated_request_ids": []}.
    """
    refreshed_credentials_json = get_refreshed_credentials_json(
        google_credentials.get_secret_value()
    )
    server = MCPServerStdio(
        command="uv",
        args=["run", "python", "-m", "mcp_server.gmail.server"],
        env={
            "GOOGLE_CREDENTIALS": refreshed_credentials_json,
        },
    )

    agent = Agent(
        model=get_pydanticai_openai_llm(),
        toolsets=[server],
        output_type=CheckRequestUpdateOutput,
    )
    result = await agent.run(
        f"From these request IDs: {', '.join(check_request_ids)} "
        "Use gmail mcp to check my inbox."
        'return only: {"updated_request_ids": [string]}. '
        'If none, return {"updated_request_ids": []}.'
    )
    return result.output


async def check_request_update_with_ctx(
    ctx: RunContext[GoogleTokenMixin], check_request_ids: list[str]
):
    return await check_request_update(check_request_ids, ctx.deps.google_token)


check_request_update_tool = Tool(
    check_request_update_with_ctx, takes_ctx=True, name="check_request_update"
)
