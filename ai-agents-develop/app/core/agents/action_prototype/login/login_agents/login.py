from typing import Callable, Literal

from alltrue.agents.schema.action_execution import PlainTextLog
from browser_use import Agent as BrowserUseAgent
from browser_use import Controller
from pydantic import BaseModel, Field

from app.core.agents.action_prototype.login.login_agents.mfa import get_otp
from app.core.agents.utils.browser_utils.hook_function import (
    generate_model_output_logs,
    generate_screenshot_logs,
)
from app.core.graph.deps.base_deps import BrowserDeps
from app.core.llm.browser_use_llm import get_browser_use_llm

login_task = """
Goal: Login to the application.

WorkFlow:
If there is no login required, stop here. Otherwise, login with x_user and x_password (the tag "<secret>" must be retained for use in actions"), stop here. You MUST STOP when you see MFA token is needed, DO NOT try to type the MFA token.


Instructions:
{instructions}

Final Step: Tell me is the login successful. You must only answer "yes" or "no". Tell me is there a MFA code required? You must only answer "yes" or "no".
"""


class LoginResponse(BaseModel):
    successful_login: Literal["yes", "no"]
    message: str = Field(..., description="Message from the login process")
    MFA_required: Literal["yes", "no"]


MFA_task = """
    Goal: Enter the MFA code

    WorkFlow: Enter the MFA code: {} and submit
    usually the page jumps to the main page after the MFA code is successfully entered, stop here.

    Final Step: Tell me is the login successful. You must only answer "yes" or "no".
"""


class MFAResponse(BaseModel):
    successful_login: Literal["yes", "no"]
    message: str = Field(..., description="Message from the login process")


class FinalResponse(BaseModel):
    successful_login: Literal["yes", "no"]
    message: str = Field(..., description="Message from the login process")


async def authenticate(
    instructions: str,
    username: str,
    password: str,
    initial_actions: list,
    browser_deps: BrowserDeps,
    add_log: Callable,
    mfa_secret: str | None = None,
    max_steps: int = 5,
) -> FinalResponse:
    async def hook_on_step_end(agent: BrowserUseAgent):
        model_output_logs = generate_model_output_logs(agent)
        screenshot_logs = generate_screenshot_logs(agent)

        await add_log(model_output_logs + screenshot_logs)

    # login required
    sensitive_data = {"x_user": username, "x_password": password}

    controller = Controller(
        output_model=LoginResponse, exclude_actions=["google_search"]
    )
    llm = get_browser_use_llm(provider="gemini", model_name="gemini-2.5-flash")
    agent = BrowserUseAgent(
        initial_actions=initial_actions,
        browser_session=browser_deps.browser_session,
        task=login_task.format(instructions=instructions),
        sensitive_data=sensitive_data,
        llm=llm,
        controller=controller,
        file_system_path=browser_deps.execution_space_path / "file_system",
    )
    await add_log(PlainTextLog(data="Running login action"))
    result = await agent.run(
        max_steps=max_steps,
        on_step_end=hook_on_step_end,
    )
    answer = result.final_result()
    await add_log(PlainTextLog(data=f"Login action result: {str(answer)}"))
    if answer:
        login_response = LoginResponse.model_validate_json(answer)

        # the case that there is MFA required
        if login_response.MFA_required.lower() == "yes":
            if not mfa_secret:
                return FinalResponse(
                    successful_login="no",
                    message="MFA secret is needed but not provided",
                )
            for i in range(5):
                otp_code = get_otp(mfa_secret)
                await add_log(PlainTextLog(data=f"Use MFA: {otp_code}"))
                agent = BrowserUseAgent(
                    browser_session=browser_deps.browser_session,
                    task=MFA_task.format(otp_code),
                    llm=llm,
                    controller=Controller(
                        output_model=MFAResponse,
                        exclude_actions=["google_search"],
                    ),
                    file_system_path=browser_deps.execution_space_path / "file_system",
                )
                result = await agent.run(
                    max_steps=max_steps,
                    on_step_end=hook_on_step_end,
                )
                answer = result.final_result()
                await add_log(PlainTextLog(data=f"MFA action result: {str(answer)}"))
                mfa_response = MFAResponse.model_validate_json(answer)
                if mfa_response.successful_login.lower() == "yes":
                    return FinalResponse(
                        successful_login="yes",
                        message=f"{login_response.message} and {mfa_response.message}",
                    )
                else:
                    await add_log(
                        PlainTextLog(
                            data=f"MFA action result: {str(answer)}, try {i+1} times"
                        )
                    )

            else:
                return FinalResponse(
                    successful_login="no",
                    message=f"{login_response.message} and {mfa_response.message}",
                )

        else:
            # the case that there is no MFA required
            if login_response.successful_login.lower() == "yes":
                return FinalResponse(successful_login="yes", message=str(answer))
            else:
                return FinalResponse(successful_login="no", message=str(answer))
    else:
        raise ValueError("Agent exited without returning a response")
