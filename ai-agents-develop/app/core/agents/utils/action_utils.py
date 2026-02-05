from typing import List

import logfire
from alltrue.agents.schema.control_execution import LocalEvidence, S3Evidence
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.messages import ModelMessage
from pydantic_ai.output import OutputDataT
from pydantic_ai.run import AgentRunResult
from pydantic_ai.tools import AgentDepsT
from pydantic_graph import GraphRunContext

from app.core.agents.compliance_agent.models import ComplianceInput
from app.core.agents.utils.summary_generator import generate_summary
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State
from app.exceptions.control_exceptions import PauseExecution
from app.utils.file_upload.file_upload import upload_file


async def store_action_execution(
    result: dict,
    ctx: GraphRunContext[State, GraphDeps],
) -> dict:
    logfire.info("Storing Action Execution Output")
    try:
        action_summary = await generate_summary(result)
    except Exception as e:
        logfire.warning(
            "Summary generation failed; storing without summary", error=str(e)
        )
        action_summary = "Unable to generate summary"
    action_execution_feedback = {
        **result,
        "action_summary": action_summary,
    }
    ctx.state.store_output(action_execution_feedback)
    logfire.info("Finished storing Action Execution Output")
    return action_execution_feedback


async def store_action_execution_screenshots(
    result: dict,
    ctx: GraphRunContext[State, GraphDeps],
    action_deps: ActionDeps,
) -> dict:
    logfire.info("Storing Action Execution Output")
    try:
        action_summary = await generate_summary(result)
    except Exception as e:
        logfire.warning(
            "Summary generation failed; storing without summary", error=str(e)
        )
        action_summary = "Unable to generate summary"
    # Upload if there is evidence created at action level
    action_evidence = ComplianceInput(**result)

    feedback_screenshots: List[S3Evidence | LocalEvidence] = []
    if action_evidence.evidence is not None:
        # Upload action evidence to S3
        for evidence_item in action_evidence.evidence:
            # assume screenshots are always png
            feedback_screenshots.append(
                upload_file(
                    evidence_item.path,
                    {"action_exec_id": action_deps.action_id},
                )
            )
    logfire.info(f"Feedback Screenshots uploaded: {feedback_screenshots}")
    action_execution_feedback = {
        **result,
        "action_summary": action_summary,
        "feedback_screenshots": [
            feedback_screenshot.model_dump()
            for feedback_screenshot in feedback_screenshots
        ],
    }
    ctx.state.store_output(action_execution_feedback)
    logfire.info("Finished storing Action Execution Output")
    return action_execution_feedback


def get_message_history_for_resume(
    ctx: GraphRunContext[State, GraphDeps],
) -> List[ModelMessage]:
    """Get stored message history from state for pause/resume functionality"""
    message_history = ctx.state.get_agent_messages()
    logfire.info(
        f"Restoring {len(message_history)} messages from state for pause/resume"
    )
    return message_history


def store_message_history_after_run(
    ctx: GraphRunContext[State, GraphDeps], result: AgentRunResult[OutputDataT]
) -> None:
    """Store new agent messages in state after an agent run for pause/resume functionality"""
    new_messages = result.new_messages()
    ctx.state.store_agent_messages(new_messages)
    logfire.info(f"Stored {len(new_messages)} new messages to state for pause/resume")


async def run_agent_with_history(
    agent: Agent[AgentDepsT, OutputDataT],
    prompt: str,
    deps: AgentDepsT,
    graph_ctx: GraphRunContext[State, GraphDeps],
    use_history: bool = True,
    **kwargs,
) -> AgentRunResult[OutputDataT]:
    """
    Run an agent with optional message history for pause/resume.

    Args:
        use_history: Whether to use stored message history (default: True)
    """
    message_history = []

    if use_history:
        message_history = get_message_history_for_resume(graph_ctx)

    with capture_run_messages() as new_messages:
        try:

            # result = None
            result = await agent.run(
                prompt, deps=deps, message_history=message_history, **kwargs
            )

            if (
                use_history
            ):  # this may not be needed when using the raise PauseExecution method
                store_message_history_after_run(graph_ctx, result)

            return result

        except PauseExecution as pause_exc:
            logfire.info(f"Agent execution paused: {pause_exc.data}")

            if use_history:
                logfire.info("Storing messages to state due to pause")
                graph_ctx.state.store_agent_messages(new_messages)

            # Re-raise the exception so the calling code can handle it appropriately
            raise pause_exc
