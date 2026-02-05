import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic import Field
from pydantic.dataclasses import dataclass
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State


@dataclass
class Pause(BaseNode[State]):
    paused_at: str
    state: State | None = None
    extra_instructions: str = Field(default="")

    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running Pause Agent")
        action_deps = ctx.deps.get_action_deps()

        # await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)
        result_dict = None
        # if not self.state:
        #     return self

        ctx.deps.node_ind = ctx.state.node_ind

        try:
            match self.paused_at:
                case "CustomQuestionnaireAssistant":
                    from app.core.agents.action_prototype.custom_questionnaire_assistant.action import (
                        CustomQuestionnaireAssistant,
                    )

                    return CustomQuestionnaireAssistant()
                case "FileCollectionAgent":
                    from app.core.agents.action_prototype.audit_file_collection_agent.action import (
                        FileCollectionAgent,
                    )

                    return FileCollectionAgent()
                case "AuditAnalysisConnectedAgents":
                    from app.core.agents.action_prototype.audit_analysis_connected_agents.action import (
                        AuditAnalysisConnectedAgents,
                    )

                    return AuditAnalysisConnectedAgents()
                case "AuditAnalysisConnectedAgentsPart2":
                    from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.action import (
                        AuditAnalysisConnectedAgentsPart2,
                    )

                    return AuditAnalysisConnectedAgentsPart2()
                case "Counter":
                    from app.core.agents.action_prototype.counter.action import Counter
                    from app.core.agents.action_prototype.counter.schema import Start

                    if not self.state:
                        return self

                    state_output = self.state.output or []
                    last_iteration_state = next(
                        (
                            o
                            for o in reversed(state_output)
                            if isinstance(o, dict) and o
                        ),
                        None,
                    )
                    if last_iteration_state:
                        return Counter(
                            resume=Start.model_validate(last_iteration_state)
                        )
                    logfire.warning(
                        "Pause: no prior Counter state found; starting fresh."
                    )
                    return Counter()
                case "Supervisor":
                    from app.core.agents.action_prototype.supervisor_agent.action import (
                        Supervisor,
                    )

                    return Supervisor(
                        resume=True, extra_instructions=self.extra_instructions
                    )
                case _:
                    raise ValueError(f"Unknown paused_at value: {self.paused_at}")

        except Exception as e:
            logfire.error(f"Error in Pause Agent: {e}")
            if result_dict is None:
                result_dict = {
                    "feedback": "Problem running the Pause Agent",
                    "reason": str(e),
                }
            await store_action_execution(result_dict, ctx)
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED, error=str(e)
            )
            raise
