from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.custom_questionnaire_assistant.schema import (
    CustomQuestionnaireAssistantNodeDeps,
    CustomQuestionnaireAssistantOutput,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant.tool import (
    custom_questionnaire_assistant,
)
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State


@dataclass
class CustomQuestionnaireAssistant(BaseNode[State]):
    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running Custom Questionnaire Assistant Action")
        ctx.state.node_ind = ctx.deps.node_ind
        # Update the action status to running
        action_deps = ctx.deps.get_action_deps()

        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None
        try:
            current_deps = CustomQuestionnaireAssistantNodeDeps.model_validate(
                ctx.deps.get_current_deps(ctx.state.output)
            )
            logfire.info(f"Input: {current_deps}")

            async with patched_action_deps(ctx, action_deps) as new_ctx:
                res = await custom_questionnaire_assistant(
                    ctx=new_ctx,
                    sheet_url=current_deps.sheet_url,
                    context_document_url=current_deps.context_document_url,
                    goal=current_deps.goal,
                )
            logfire.info(f"Result: {res}")

            result = CustomQuestionnaireAssistantOutput.model_validate(res)
            result_dict = result.model_dump()
            result_with_feedback = await store_action_execution(result_dict, ctx)
            # Update the action status to success, also store the output
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )

            logfire.info(f"Output: {result_with_feedback}")

            return await ctx.deps.get_next_node()

        except Exception as e:
            logfire.error(f"Error in Custom Questionnaire Assistant Action: {e}")
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the CustomQuestionnaireAssistant Agent",
                    "reason": str(e),
                }
            result_with_feedback = await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
