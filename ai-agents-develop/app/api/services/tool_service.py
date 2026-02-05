from typing import List

from alltrue.agents.schema.tools import Tool

from app.core.llm.model_selector import ModelSelector
from app.core.registry import TOOLS_REGISTRY


def get_all_tools() -> List[Tool]:
    """
    Return a serializable list of registered tools.
    """
    tools: List[Tool] = []
    for tool_id, bundle in TOOLS_REGISTRY.items():
        tools.append(
            Tool(
                tool_id=tool_id,
                tool_display_name=bundle.tool_display_name,
                tool_description=bundle.tool_description,
                default_model=bundle.default_model,
                allowed_models=ModelSelector.get_all_allowed_models(
                    allowed_model_criteria=bundle.allowed_model_criteria
                ),
            )
        )

    return tools
