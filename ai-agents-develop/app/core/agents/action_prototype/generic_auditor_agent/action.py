from dataclasses import dataclass
from typing import Literal

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic import BaseModel, Field, ValidationError
from pydantic_ai import Agent, RunContext, Tool
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.generic_auditor_agent.schema import (
    GenericAuditorAgentDeps,
    GenericAuditorAgentOutput,
)
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.save_locally import (
    save_locally,
)
from app.core.agents.action_prototype.generic_auditor_agent.supervisor_tools.tools import (
    SupervisorTools,
)
from app.core.agents.compliance_agent.models import EvidenceItem
from app.core.agents.utils.action_utils import store_action_execution_screenshots
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

SUPERVISOR_PROMPT = """
    Your job is to control three tools to fulfill user tasks related to website navigation, login, and file processing.
    You do not directly access websites or files; you only operate via these tools.
    Available Tools:
        • login(login_url, username, password, login_instructions, mfa_secret):
        Logs into a website using provided credentials and login_instructions.
        Returns: JSON with successful_login: "yes" (success) or "no" (failure).

        • navigation(instructions, goal, initial_url, screenshot_target_information, page_audit_check_information):
        Navigates a website from initial_url using step-by-step instructions to achieve a goal and locate screenshot_target_information.
        Returns: JSON with success (bool), current_url (str), feedback (str), and downloaded_files (list of str or None).

        • files_process(instructions, file_names):
        Processes files with specified file_names as per the provided instructions.

    Instructions:

        1. Analyze the user’s request and determine which tools are needed and their correct order.

        2. Tool usage:
        • Always use tools sequentially, never in parallel.
        • Do not skip required steps; each tool must be used in the correct order.

        3. login():

            • Run login() first if access to a secure/personalized site is needed.

            • If `successful_login` is "no", halt and report the failure.

            • If "yes", do not repeat login unless a prompt change requires re-authentication.


        4. navigation():

            • Use navigation() for all multi-step web actions (e.g., clicking, searching, browsing, selecting, finding items).

            • Parse/generate all required arguments from the prompt (`instructions`, `goal`, `initial_url`, `screenshot_target_information`, `page_audit_check_information`).

            • If `screenshot_target_information` or `page_audit_check_information` is empty ("" or omitted), exclude that field in the call.

            • If screenshots are required, ensure instructions reflect this, and pass screenshot_target_information.

            • When you pass `screenshot_target_information`, you might need to modify the screenshot_target_information, to make sure it only contains the information that is needed to be extracted from the website. Do not include any information like "taking screenshot" or "I want you to do".

            • Never invent or add actions (e.g., clicks) that the user did not specify. Only follow user-provided instructions.

            • Review the downloaded_files field to determine if subsequent file processing is required.

        5. files_process():

            • Use when the prompt requires extracting or analyzing data from downloaded files.

            • Only run after navigation() if file downloads are involved.

            • If `downloaded_files` returned by navigation() is empty, skip files_process.

            • If `downloaded_files` is not empty but file processing is not requested, skip files_process.

    General Rules:

        • Always extract and generate all tool arguments unless explicitly provided by the user.

        • If no tool is needed, state this clearly and concisely.

        • If any step fails, retry that step up to two times. If all attempts fail, stop and report the failure; do not proceed.

        • Never make assumptions about missing steps or user intent beyond the prompt.

    Example Tool Flow:

        • login → navigation

        • login → navigation → files_process

        • navigation

        • navigation → files_process

        • No tools (if prompt is informational only)

    Final Output:
        • You need to answer if the whole process is successful or not, and provide feedback.

    """


class GeneralResponse(BaseModel):
    successful: Literal["yes", "no"] = Field(
        description=f"yes or no, whether the whole process was successful"
    )
    feedback: str


class SupervisorNodeException(Exception):
    """Custom exception raised for errors in the GenericAuditorAgent run."""


@dataclass
class GenericAuditorAgent(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running the GenericAuditorAgent action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running

        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()

        action_deps = ctx.deps.get_action_deps()

        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            self.current_deps = GenericAuditorAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
        except ValidationError as ve:
            await action_deps.update_action_status(
                ActionExecutionStatus.FAILED, error=str(ve)
            )
            raise SupervisorNodeException(
                f"Invalid dependencies for GenericAuditorAgent: {ve}"
            ) from ve
        async with patched_action_deps(ctx, action_deps) as new_ctx:
            output = await self.run_supervisor(new_ctx)

        # ==== end logic ====
        result = output.model_dump()
        result_with_feedback = await store_action_execution_screenshots(
            result=result, ctx=ctx, action_deps=action_deps
        )
        # Update the action status to success, also store the output
        await action_deps.update_action_status(
            ActionExecutionStatus.PASSED, output=result_with_feedback
        )
        logfire.info(f"Output: {ctx.state.output}")
        return await ctx.deps.get_next_node()

    async def run_supervisor(self, ctx: RunContext[ActionDeps]) -> GeneralResponse:
        """
        Run the supervisor agent based on the user prompt.
        """
        try:
            # this is a mutable object that will hold the updated cookie string
            supervisor_tool_set = SupervisorTools()
            agent = Agent(
                system_prompt=SUPERVISOR_PROMPT,
                model=get_pydanticai_openai_llm(),
                tools=[
                    Tool(
                        supervisor_tool_set.login_run,
                        takes_ctx=True,
                        name="login",
                    ),
                    Tool(
                        supervisor_tool_set.navigation_run,
                        takes_ctx=True,
                        name="navigation",
                    ),
                    Tool(
                        supervisor_tool_set.files_process,
                        takes_ctx=True,
                        name="files_process",
                    ),
                ],
                output_type=GeneralResponse,
            )
            target_info = (
                f"""The screenshot target information is:
                {{{self.current_deps.screenshot_target_information}}}"""
                if self.current_deps.screenshot_target_information
                else ""
            )
            check_info = (
                f"""The page audit check information is:
                {{{self.current_deps.page_audit_check_information}}}"""
                if self.current_deps.page_audit_check_information
                else ""
            )
            agent_result = await agent.run(
                user_prompt=f"""
                The user's prompt is:
                {self.current_deps.user_prompt}
                The login information is:
                input_url: {self.current_deps.login_url}, username: {self.current_deps.username}, password: {self.current_deps.password}, login_instructions: {self.current_deps.login_instructions}, MFA secret: {self.current_deps.mfa_secret}
                {target_info}
                {check_info}
                """,
                deps=ctx.deps,
            )
            if not supervisor_tool_set.navigation_successful:
                logfire.error("failed navigation")
                await supervisor_tool_set.failed_log(ctx.deps.working_dir)
            supervisor_tool_set.save_browser_info(ctx.deps.working_dir)
            if not agent_result:
                raise ValueError("Agent exited without returning a response")
            save_locally(
                str(agent_result.all_messages()),
                ctx.deps.working_dir,
                "supervisor_log.txt",
            )

            evidence = []
            for i in supervisor_tool_set.browser_info.screenshot_info:
                for j in i.stored_images:
                    evidence.append(
                        EvidenceItem(
                            object_type="file",
                            path=j,
                        )
                    )

            res = GenericAuditorAgentOutput(
                **agent_result.output.model_dump(),
                evidence=evidence,
                screenshot_info=[
                    i.model_dump()
                    for i in supervisor_tool_set.browser_info.screenshot_info
                ],
            )
            return res
        except Exception as e:
            logfire.error(f"Web supervisor Node failed: {e}")
            raise SupervisorNodeException(f"Web supervisor Node failed: {e}") from e
