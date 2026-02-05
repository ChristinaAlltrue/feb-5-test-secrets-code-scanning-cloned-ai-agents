import re
from typing import Callable

import logfire
from alltrue.agents.schema.action_execution import SubagentNode
from pydantic_ai import Agent, RunContext

from app.core.agents.action_prototype.bundles import ToolBundle
from app.core.agents.action_prototype.supervisor_agent.prompt import (
    SUPERVISOR_SYSTEM_PROMPT,
)
from app.core.agents.action_prototype.supervisor_agent.schema import SupervisorAgentDeps
from app.core.agents.base_node.base_node import AgentBaseNode
from app.core.agents.utils.tool_wrapper import (
    ToolConfiguration,
    create_validated_tool_callable,
)
from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.llm.model_registry import ModelRegistry


def create_sub_agent_delegation_tool(
    tool_id: str, current_agent: Agent, subagent_display_name: str
) -> Callable:
    """Creates a function that calls a sub-agent."""

    async def dynamic_sub_agent_tool(
        ctx: RunContext[ToolActionDeps], user_query: str
    ) -> str:
        logfire.info(
            f"Delegating to sub-agent {subagent_display_name} '{tool_id}' with query: {user_query}"
        )
        result = await current_agent.run(user_query, deps=ctx.deps, usage=ctx.usage)
        return result.output

    dynamic_sub_agent_tool.__doc__ = f"An intelligent sub-agent."
    sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", subagent_display_name)
    dynamic_sub_agent_tool.__name__ = sanitized_name
    return dynamic_sub_agent_tool


@logfire.instrument()
def build_agent_from_node(
    node: SubagentNode, tool_registry: dict[str, "ToolBundle"]
) -> Callable:
    agent_tools = []
    child_subagent_index = 0
    for child_node in node.children:
        if child_node.type == "subagent":
            child_delegation_tool = build_agent_from_node(child_node, tool_registry)
            agent_tools.append(child_delegation_tool)
            child_subagent_index += 1
        else:
            tool_bundle = tool_registry[child_node.tool_id]
            agent_tools.append(
                create_validated_tool_callable(
                    tool_bundle,
                    tool_config_from_deps=ToolConfiguration.model_validate(
                        child_node, from_attributes=True
                    ),
                )
            )

    current_agent = Agent(
        model=ModelRegistry.get_pydantic_ai_llm(
            node.selected_model,
        ),
        deps_type=SupervisorAgentDeps,
        instructions=node.prompt,
        system_prompt=AgentBaseNode.complete_system_prompt(SUPERVISOR_SYSTEM_PROMPT),
        tools=agent_tools,
        instrument=True,
    )

    return create_sub_agent_delegation_tool(
        node.tool_id,
        current_agent,
        node.tool_display_name,
    )
