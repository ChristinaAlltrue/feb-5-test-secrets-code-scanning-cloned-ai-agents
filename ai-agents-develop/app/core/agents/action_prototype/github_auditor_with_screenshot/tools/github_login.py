from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import RunContext, Tool

from app.core.agents.action_prototype.login.tool import login
from app.core.graph.deps.action_deps import ActionDeps


async def github_login(ctx: RunContext[ActionDeps]):
    await ctx.deps.add_log(
        PlainTextLog(data="Starting github login process"),
    )
    username = ctx.deps.model_extra.get("username")
    password = ctx.deps.model_extra.get("password")
    mfa_secret = ctx.deps.model_extra.get("mfa_secret")
    if not username or not password:
        raise ValueError(
            "Missing required credentials: 'username' and 'password' are required."
        )

    login_resp = await login(
        ctx,
        initial_url="https://github.com/login",
        username=username,
        password=password,
        instructions="""
        login to github with the given username and password.
        """,
        mfa_secret=mfa_secret,
        max_steps=10,
    )
    if login_resp.successful == "no":
        await ctx.deps.add_log(
            [
                PlainTextLog(data="Failed to login to github"),
                ObjectLog(data=login_resp.model_dump()),
            ]
        )
        return login_resp

    await ctx.deps.add_log(
        [
            PlainTextLog(data="Successfully logged in to github"),
            ObjectLog(data=login_resp.model_dump()),
        ]
    )
    return login_resp


github_login_tool = Tool(github_login, takes_ctx=True)
