import os
from typing import Literal

import logfire
from pydantic_ai import RunContext

from app.core.agents.action_prototype.file_inspection.tools import file_process
from app.core.agents.action_prototype.general_browser.schema import GeneralBrowserOutput
from app.core.agents.action_prototype.general_browser.tool import general_browser
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.browser_info import (
    BrowserInfo,
)
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.failed_log import (
    failed_log_generator,
)
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.save_locally import (
    save_locally,
)
from app.core.agents.action_prototype.login.tool import login
from app.core.graph.deps.action_deps import ActionDeps

# Not too sure how smart MCP can be. This is the first try to see how much it can do.
# Because of that I create the tool to let the supervisor agent to call the MCP server tool
# If it is smart enough, we can combine the two agents into one.


class ScreenshotToolException(Exception):
    """Custom exception raised for errors in the screenshot tool."""


class LoginToolException(Exception):
    """Custom exception raised for errors in the login tool."""


class NavigationToolException(Exception):
    """Custom exception raised for errors in the navigation tool."""


class FileToolException(Exception):
    """Custom exception raised for errors in the file tool."""


class SupervisorTools:
    browser_info: BrowserInfo
    file_process_result: str
    navigation_feedback: str
    navigation_successful: bool

    def __init__(self):
        self.browser_info = BrowserInfo()
        self.file_process_result = ""
        self.navigation_feedback = ""
        self.navigation_successful = False

    async def login_run(
        self,
        ctx: RunContext[ActionDeps],
        instructions: str,
        login_url: str,
        username: str,
        password: str,
        mfa_secret: str = "",
        max_steps: int = 8,
    ) -> Literal["yes", "no"]:
        logfire.info("Running login action")
        try:
            # === logic ===
            result = await login(
                ctx,
                initial_url=login_url,
                username=username,
                password=password,
                instructions=instructions,
                mfa_secret=mfa_secret,
                max_steps=max_steps,
            )
            # ==== end logic ====

            successful = result.successful
            if successful == "no":
                raise LoginToolException(f"Login action failed: {result.feedback}")
            return successful

        except Exception as e:
            logfire.error(f"Error in Login action: {e}")
            raise LoginToolException(f"Login action failed: {e}") from e

    async def navigation_run(
        self,
        ctx: RunContext[ActionDeps],
        instructions: str,
        goal: str,
        initial_url: str,
        target_information: str = "",
        check_information: str = "",
    ) -> str:
        logfire.info("Running navigation action")

        try:
            # === logic ===
            res = await general_browser(
                ctx,
                instructions,
                goal,
                initial_url,
                target_information,
                audit_instructions=check_information,
                generated_info=self.browser_info,
            )
            # ==== end logic ====
            result = GeneralBrowserOutput.model_validate(res)
            success = result.successful
            self.navigation_feedback = result.feedback
            if success == "no":
                self.navigation_successful = False
                raise
            elif success == "yes":
                self.navigation_successful = True
            ret = result.model_dump_json()
            return ret
        except Exception as e:
            logfire.error(f"Error in Navigation action: {e}")
            raise NavigationToolException(f"Navigation action failed: {e}") from e

    def save_browser_info(
        self, working_dir: str, file_name: str = "browser_info.txt"
    ) -> None:
        """Save the browser information to the working directory."""
        logfire.info("Saving browser information")
        try:
            to_be_saved = "Browser Information:\n"
            to_be_saved += str(self.browser_info.check_info) + "\n"
            to_be_saved += str(self.browser_info.screenshot_info) + "\n"
            to_be_saved += "Files Processed Results:\n"
            to_be_saved += str(self.file_process_result) + "\n"
            save_locally(to_be_saved, working_dir, file_name)
            logfire.info(f"Browser information saved to {working_dir}")
        except Exception as e:
            logfire.error(f"Error saving browser information: {e}")
            raise IOError(f"Failed to save browser info: {e}") from e

    async def files_process(
        self,
        ctx: RunContext[ActionDeps],
        instructions: str,
        file_names: list[str],
    ) -> str:
        """Process the files, first input is the instruction, second is the file names."""
        logfire.info("Running files processing action")
        working_dir = ctx.deps.working_dir
        file_path_list = []
        for file in file_names:
            file_path = os.path.join(working_dir, file)
            if os.path.commonpath([file_path, working_dir]) == working_dir:
                file_path_list.append(file_path)
            else:
                raise ValueError(f"Invalid file path: {file}")
        try:
            # === logic ===
            res = await file_process(
                ctx,
                instructions=instructions,
                file_path_list=file_path_list,
            )
            # ==== end logic ====
            logfire.info(f"Files processing result: {res}")
            self.file_process_result = res
            return res
        except Exception as e:
            logfire.error(f"Error in Files Processing action: {e}")
            raise FileToolException(f"Files Processing action failed: {e}") from e

    async def failed_log(self, working_dir: str) -> None:
        """Log the failure details."""
        navigation_feedback: str
        if not self.navigation_successful:
            navigation_feedback = self.navigation_feedback
            fail_res = await failed_log_generator(navigation_feedback)
            to_be_saved = "Failed reason:\n"
            to_be_saved += fail_res
            save_locally(to_be_saved, working_dir, "browser_failed_reason.txt")
