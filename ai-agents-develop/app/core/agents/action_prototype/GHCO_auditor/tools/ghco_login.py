# TODO: These tools should be replaced with the generic browser agents

from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import RunContext, Tool

from app.core.agents.action_prototype.login.tool import login
from app.core.graph.deps.action_deps import ActionDeps


async def ghco_login(
    ctx: RunContext[ActionDeps],
    login_url: str,
):
    await ctx.deps.add_log(
        PlainTextLog(data="Starting ghco login process"),
    )
    username = ctx.deps.model_extra.get("username")
    password = ctx.deps.model_extra.get("password")
    if not username or not password:
        raise ValueError(
            "Missing required credentials: 'username' and 'password' are required."
        )

    login_resp = await login(
        ctx,
        initial_url=login_url,
        username=username,
        password=password,
        instructions="""
        if you cannot see username and password fields, you are logged in. Task Completed
        If already logged in, proceed to the next step. Do not log out.
        """,
        max_steps=10,
    )
    if login_resp.successful == "no":
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Failed to login to ghco"),
                ObjectLog(data=login_resp.model_dump()),
            ]
        )
        raise ValueError("Failed to login to ghco")

    await ctx.deps.add_log(
        [
            PlainTextLog(data="Successfully logged in to ghco"),
            ObjectLog(data=login_resp.model_dump()),
        ]
    )
    return login_resp


ghco_login_tool = Tool(ghco_login, takes_ctx=True)
