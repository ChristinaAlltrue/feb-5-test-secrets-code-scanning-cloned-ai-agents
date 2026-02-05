from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.audit_analysis_browser_agent.schema import (
    AuditAnalysisBrowserAgentDeps,
)
from app.core.agents.action_prototype.generic_browser_agent.generic_browser_agent_playwright import (
    generic_browser_agent_playwright,
)
from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentDeps,
)
from app.core.agents.utils.storage_utils import generate_storage_state_path
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class AuditAnalysisBrowserAgent(BaseNode[State]):
    """
    Browser Agent for auditing workflow.
    Handles web automation, login, navigation, and file downloads.
    """

    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running Audit Analysis Browser Agent")
        ctx.state.node_ind = ctx.deps.node_ind

        # Initialize browser if needed
        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps()

        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        try:
            # Validate input parameters using schema
            current_deps = AuditAnalysisBrowserAgentDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            # Extract parameters from validated schema
            # target_business_unit = ctx.deps.get_current_deps(ctx.state.output).get("target_business_unit", [])
            target_url = (
                current_deps.target_url.strip() if current_deps.target_url else ""
            )
            task = current_deps.task
            username = current_deps.username
            password = current_deps.password

            # Validate required fields for storage state path generation
            if not target_url:
                raise ValueError("target_url is required and cannot be empty")
            if not username:
                raise ValueError("username is required and cannot be empty")

            # Generate storage state path from domain+username or use provided one
            storage_state_path = current_deps.storage_state_path
            if not storage_state_path:
                storage_state_path = generate_storage_state_path(
                    target_url, username, password
                )

            logfire.info(f"Browser Agent parameters - Target URL: {target_url}")

            # # Attach credentials to action deps to avoid passing them by LLM
            # action_deps.model_extra.update(
            #     {
            #         "username": username,
            #         "password": password,
            #     }
            # )

            logfire.info(f"storage_state_path: {storage_state_path}")

            updated_action_deps = GenericBrowserAgentDeps(
                **vars(action_deps),
                **{
                    "username": username,
                    "password": password,
                    "storage_state_path": storage_state_path,
                },
            )

            async with patched_action_deps(ctx, updated_action_deps) as new_ctx:
                # Navigate and download files
                logfire.info("Navigating and downloading files")
                browser_result = await generic_browser_agent_playwright(
                    new_ctx,
                    task,
                    target_url,
                    # model_name="gpt-4.1",
                )

                # await generic_browser_agent_playwright(
                #     new_ctx,
                #     task=task,
                #     max_steps=30,
                #     model_name="gpt-4.1",
                #     use_vision=False,
                # )  # previous interface for other implementations

                if browser_result.successful != "yes":
                    raise ValueError(
                        f"Browser navigation failed: {browser_result.feedback}"
                    )

                files_count = len(browser_result.files) if browser_result.files else 0
                logfire.info(
                    f"Browser agent completed - Downloaded {files_count} files"
                )

            # Prepare output for next agent
            browser_output = {
                "successful": browser_result.successful == "yes",
                "feedback": browser_result.feedback,
                "execution_flow": browser_result.execution_flow,
                "files": browser_result.files or [],
                # "business_units": target_business_unit,
                "downloaded_count": (
                    len(browser_result.files) if browser_result.files else 0
                ),
            }

            ctx.state.store_output(browser_output)

            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=browser_output
            )

            logfire.info("Audit Analysis Browser Agent completed successfully")
            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Audit Analysis Browser Agent failed: {e}")
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
