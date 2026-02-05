from typing import Any, Callable, Optional

import logfire
from pydantic_ai import RunContext

from app.core.agents.action_prototype.bundles import ToolBundle
from app.core.agents.action_prototype.supervisor_agent.schema import ToolConfiguration
from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.llm.model_selector import ModelSelector


def create_validated_tool_callable(
    bundle: ToolBundle, tool_config_from_deps: Optional[ToolConfiguration] = None
) -> Callable[..., Any]:
    """
    Creates a callable wrapper around a ToolBundle's function that performs
    model validation before invoking the actual tool.
    """
    original_pydantic_ai_tool = bundle.function  # The pydantic_ai.Tool instance
    original_pydantic_ai_tool_function = (
        original_pydantic_ai_tool.function
    )  # The actual function inside the Tool

    logfire.info(
        f"Creating validated tool callable for bundle with tool config from deps: {tool_config_from_deps}"
    )

    # @wraps(original_pydantic_ai_tool_function) # Wrap the pydantic_ai.Tool instance directly
    async def validated_tool_callable(*args, **kwargs) -> Any:
        logfire.info(
            f"Validated tool callable invoked with args: {args} and kwargs: {kwargs}"
        )

        # The selected model as defined in SupervisorAgentDeps for this specific tool
        user_selected_model: Optional[str] = (
            tool_config_from_deps.selected_model if tool_config_from_deps else None
        )

        final_selected_model_id: Optional[str] = None

        if bundle.default_model is None:
            raise ValueError("No bundle default model provided for validation.")

        final_selected_model_id = ModelSelector.validate_and_get_model_id(
            proposed_model_id=user_selected_model,
            default_model=bundle.default_model,
            allowed_model_criteria=bundle.allowed_model_criteria,
        )

        if not final_selected_model_id:
            logfire.error(
                "Final selected model ID is None or empty after validation. This should not happen."
            )
            raise ValueError(
                "Final selected model ID is None or empty after validation."
            )

        # set param in ctx.deps (which is in args[0]) if applicable
        if args and isinstance(args[0], RunContext):
            ctx: RunContext[ToolActionDeps] = args[0]
            if hasattr(ctx, "deps"):
                ctx.deps.selected_model = final_selected_model_id

        return await original_pydantic_ai_tool_function(*args, **kwargs)

    bundle.function.function = validated_tool_callable
    bundle.function.function_schema.function = validated_tool_callable

    logfire.debug(f"Bundle function after wrapping: {bundle.function}")
    logfire.debug(f"Original pydantic_ai tool: {original_pydantic_ai_tool}")

    return original_pydantic_ai_tool
