import re
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionStatus
from alltrue.agents.schema.control_execution import LocalEvidence, S3Evidence
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.base_action_schema.deps_schema import BaseActionDeps
from app.core.agents.base_action_schema.output_schema import BaseActionOutput
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.state.state import State
from app.utils.file_upload.file_upload import upload_file

T = TypeVar("T", bound=BaseActionDeps)  # Input deps type
R = TypeVar("R", bound=BaseActionOutput)  # Output type


@dataclass
class ActionLifecycleManager(Generic[T, R]):
    """
    Manages the common lifecycle of action nodes using composition.
    Handles setup, validation, execution, storage, and error handling.
    """

    # Required dependencies
    deps_type: Type[T]
    action_name: str

    # Optional customizers
    pre_execution_hook: Optional[
        Callable[[GraphRunContext[State, GraphDeps], T], Coroutine[Any, Any, None]]
    ] = None
    post_execution_hook: Optional[
        Callable[
            [GraphRunContext[State, GraphDeps], R], Coroutine[Any, Any, Dict[str, Any]]
        ]
    ] = None
    error_handler: Optional[
        Callable[
            [GraphRunContext[State, GraphDeps], Exception],
            Coroutine[Any, Any, Dict[str, Any]],
        ]
    ] = None

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
        logfire.info(f"Running {self.action_name} action")

        # 1. Setup phase
        await self._setup_action(ctx)

        try:
            # 2. Validation phase
            current_deps = await self._validate_deps(ctx)

            # 3. Pre-execution hook
            if self.pre_execution_hook:
                await self.pre_execution_hook(ctx, current_deps)

            # 4. Execution phase
            result = await business_logic(ctx, current_deps)

            # 5. Post-execution hook and storage
            output = await self._handle_success(ctx, result)

            # 6. Navigation
            return await ctx.deps.get_next_node()

        except Exception as e:
            # 7. Error handling
            await self._handle_error(ctx, e)
            raise

    async def _setup_action(self, ctx: GraphRunContext[State, GraphDeps]) -> None:
        """Setup action execution environment."""
        ctx.state.node_ind = ctx.deps.node_ind
        action_deps = ctx.deps.get_action_deps()
        await action_deps.update_action_status(ActionExecutionStatus.IN_PROGRESS)

    async def _validate_deps(self, ctx: GraphRunContext[State, GraphDeps]) -> T:
        """Validate and parse input dependencies."""
        current_deps = self.deps_type.model_validate(
            ctx.deps.get_current_deps(ctx.state.output)
        )
        logfire.info(f"Input: {current_deps}")
        return current_deps

    async def _handle_success(
        self, ctx: GraphRunContext[State, GraphDeps], result: R
    ) -> Dict[str, Any]:
        """Handle successful execution."""
        action_deps = ctx.deps.get_action_deps()

        # Apply post-execution hook if provided
        if self.post_execution_hook:
            output = await self.post_execution_hook(ctx, result)
        else:
            # Default: assume result is already a dict or has model_dump()
            if hasattr(result, "model_dump"):
                output = result.model_dump()
            else:
                output = result if isinstance(result, dict) else {"result": result}

        # Store output in state
        ctx.state.store_output(output)

        # Traversal the action exec folder and save in the state.
        logfire.info(
            f"Traversal the action exec folder and upload the evidence: {action_deps.action_working_dir}"
        )

        generated_files: List[Path] = []
        # filter out the auto-generated files like page-*.png
        pattern = re.compile(r"^page-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z\.png$")
        for file in Path(action_deps.action_working_dir).iterdir():
            if file.is_file():
                if pattern.match(file.name):
                    continue  # Skip files matching the pattern
                generated_files.append(file.resolve())
        ctx.state.store_generated_files(generated_files)

        execution_files: List[S3Evidence | LocalEvidence] = []

        # Upload the generated files to the file storage
        for file in generated_files:
            execution_files.append(
                upload_file(
                    str(file),
                    {"action_exec_id": action_deps.action_id},
                    new_file_name=f"{ctx.deps.control_info.control_execution_id}/{action_deps.action_folder_name}/{file.name}",
                )
            )
        output["execution_files"] = [file.model_dump() for file in execution_files]
        logfire.info(f"Execution files: {execution_files}")
        ctx.state.store_output(output)

        # Update action status
        await action_deps.update_action_status(
            ActionExecutionStatus.PASSED, output=output
        )

        logfire.info(f"Output: {ctx.state.output}")
        return output

    async def _handle_error(
        self, ctx: GraphRunContext[State, GraphDeps], error: Exception
    ) -> None:
        """Handle execution errors."""
        logfire.error(f"Error in {self.action_name} action: {error}")

        action_deps = ctx.deps.get_action_deps()

        # Apply custom error handler if provided
        if self.error_handler:
            error_output = await self.error_handler(ctx, error)
            ctx.state.store_output(error_output)

        # Update action status
        await action_deps.update_action_status(
            ActionExecutionStatus.ACTION_REQUIRED, error=str(error)
        )
