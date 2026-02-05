from typing import Optional

from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import RunContext

from app.core.agents.action_prototype.login.login_agents.login import authenticate
from app.core.agents.action_prototype.login.schema import LoginOutput
from app.core.graph.deps.action_deps import ActionDeps


async def login(
    ctx: RunContext[ActionDeps],
    initial_url: str,
    username: str,
    password: str,
    instructions: str,
    mfa_secret: Optional[str] = None,
    max_steps: int = 10,
) -> LoginOutput:
    """
    Tool for handling login functionality

    Args:
        initial_url (str): The starting URL
        username (str): Username to log in
        password (str): Password for the account
        instructions (str): Login flow instructions
        mfa_secret (Optional[str], optional): TOTP MFA key. Defaults to None.
        max_steps (int, optional): Maximum number of steps. Defaults to 10.

    Returns:
        LoginOutput: The result of the login attempt
    """
    before_log = [
        PlainTextLog(data="Starting login process"),
        ObjectLog(data={"url": initial_url}),
    ]
    await ctx.deps.add_log(before_log)

    # ==== logic ====
    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()

    initial_actions = [
        {"navigate": {"url": initial_url, "new_tab": False}},
    ]

    auth_result = await authenticate(
        instructions=instructions,
        username=username,
        password=password,
        initial_actions=initial_actions,
        browser_deps=browser_deps,
        add_log=ctx.deps.add_log,
        mfa_secret=mfa_secret,
        max_steps=max_steps,
    )

    result = LoginOutput(
        successful=auth_result.successful_login,
        feedback=auth_result.message,
    )
    # ==== end logic ====

    after_log = [
        PlainTextLog(data="Login process completed"),
        ObjectLog(data={"success": result.successful}),
    ]
    await ctx.deps.add_log(after_log)

    return result
