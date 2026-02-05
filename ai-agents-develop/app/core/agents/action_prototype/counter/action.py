from dataclasses import dataclass

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic import BaseModel, ValidationError
from pydantic_graph import BaseNode, End, GraphRunContext

from app.core.agents.action_prototype.counter.schema import Start
from app.core.agents.action_prototype.pause.action import Pause
from app.core.agents.utils.action_utils import store_action_execution
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State


async def load_state(
    ctx: GraphRunContext[State, GraphDeps], action_deps: ActionDeps
) -> BaseModel:
    try:
        start_model = Start.model_validate(ctx.deps.get_current_deps(ctx.state.output))
        return start_model
    except ValidationError as ve:
        await action_deps.update_action_status(
            ActionExecutionStatus.FAILED, error=str(ve)
        )
        raise ve


@dataclass
class Counter(BaseNode[State]):
    resume: Start | None = None

    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        logfire.info("Running the Counter action")
        ctx.state.node_ind = ctx.deps.node_ind
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

        if self.resume is None:
            self.current_deps: Start = await load_state(ctx, action_deps)
        else:
            self.current_deps = self.resume

        self.current_deps.number -= 1
        if self.current_deps.number > 0:
            ctx.state.store_output(self.current_deps.model_dump())
            await action_deps.update_action_status(
                ActionExecutionStatus.ACTION_REQUIRED,
                error=f"Paused: Counter not yet at zero {self.current_deps.number}",
            )
            return Pause(paused_at=self.__class__.__name__)

        elif self.current_deps.number <= 0:
            result_with_feedback = await store_action_execution(
                {"message": f"The count shifted to {self.current_deps.number}"}, ctx
            )
            await action_deps.update_action_status(
                ActionExecutionStatus.PASSED, output=result_with_feedback
            )
            ctx.state.store_output(self.current_deps.model_dump())
            return End(data=result_with_feedback)
