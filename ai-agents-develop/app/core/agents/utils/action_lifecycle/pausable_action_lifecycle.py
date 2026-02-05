from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.pause.action import Pause
from app.core.agents.base_action_schema.deps_schema import BaseActionDeps
from app.core.agents.base_action_schema.output_schema import BasePausableActionOutput
from app.core.agents.utils.action_lifecycle.action_lifecycle import (
    ActionLifecycleManager,
)
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State

T = TypeVar("T", bound=BaseActionDeps)  # Input deps type
R = TypeVar("R", bound=BasePausableActionOutput)  # Output type


@dataclass
class PausableActionLifecycleManager(ActionLifecycleManager[T, R]):
    """
    Manages the common lifecycle of pausable action nodes using composition.
    Handles setup, validation, execution, storage, and error handling.
    """

    async def execute(
        self,
        ctx: GraphRunContext[State, GraphDeps],
        business_logic: Callable[[GraphRunContext[State, GraphDeps], T], Awaitable[R]],
    ) -> BaseNode:
        """
        Execute the action with full lifecycle management.

        Args:
            ctx: Graph execution context
            business_logic: The core business logic function

        Returns:
            Next node to execute
        """
        logfire.info(
            f"Running {self.action_name} action. Execution id: {ctx.deps.control_info.control_execution_id}",
            info={
                "control_execution_id": ctx.deps.control_info.control_execution_id,
                "node_ind": ctx.state.node_ind,
                "action_name": self.action_name,
            },
        )

        # 1. Setup phase
        await self._setup_action(ctx)

        try:

            # 2. Validation phase
            current_deps = await self._validate_deps(ctx)
            action_deps = ctx.deps.get_action_deps()

            # 3. Pre-execution hook
            if self.pre_execution_hook:
                await self.pre_execution_hook(ctx, current_deps)

            # 4. Execution phase
            result: R = await business_logic(ctx, current_deps)

            if result.pause == "yes":
                ctx.state.node_ind = ctx.deps.node_ind
                if ctx.state.agent_messages:
                    ctx.state.agent_messages.pop()
                ctx.state.store_output(result.model_dump())

                await action_deps.update_action_status(
                    ActionExecutionStatus.ACTION_REQUIRED,
                    error=result.pause_reason or "Paused by agent",
                )
                # raise GraphExecutionActionRequiredException(
                #     result.pause_reason or "Paused by agent"
                # )
                return Pause(paused_at=self.action_name)

            # 5. Post-execution hook and storage
            output = await self._handle_success(ctx, result)

            # 6. Navigation
            return await ctx.deps.get_next_node()

        except Exception as e:
            # 7. Error handling
            await self._handle_error(ctx, e)
            raise
