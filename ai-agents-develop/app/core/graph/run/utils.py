from typing import List, Optional
from uuid import UUID

import logfire
from pydantic_ai.messages import ModelRequest, ToolCallPart, ToolReturnPart
from pydantic_graph import BaseNode, Graph

from app.core.graph.deps.base_deps import ControlInfo
from app.core.graph.sql_state_persistence.persistence import SqlStatePersistence
from app.core.graph.state.state import State
from app.core.models.models import ActionExecution, ControlExecution
from app.core.registry import GRAPH_NODE_REGISTRY
from app.core.storage_dependencies.repositories.providers import RepositoryProvider
from app.utils.folder_operation import (
    construct_control_execution_folder,
    setup_control_execution_folder_for_rerun,
)
from config import SQLITE_DATABASE_SYNC_URL


def create_graph(nodes: tuple[BaseNode, ...]) -> Graph[State]:
    """
    Create a graph with the given nodes.
    Add the necessary nodes to the graph.
    """
    node_set = set(nodes)
    node_set.add(GRAPH_NODE_REGISTRY["pause"])
    return Graph(
        nodes=node_set,
        state_type=State,
    )


def get_nodes_from_strings(node_names: list[str]) -> tuple[BaseNode, ...]:
    try:
        return tuple(GRAPH_NODE_REGISTRY[name] for name in node_names)
    except KeyError as e:
        raise ValueError(f"Invalid node name: {e.args[0]}") from e


async def setup_control_execution(
    provider: RepositoryProvider, control_exec_id: UUID
) -> tuple[ControlExecution, ControlInfo, list]:
    """Setup control execution and return necessary information.

    Args:
        provider: Repository provider
        control_exec_id: UUID of the control execution

    Returns:
        tuple containing:
            - ControlExecution object
            - ControlInfo object
            - list of action IDs
    """
    control_exec: Optional[ControlExecution] = await provider.get_repository(
        ControlExecution
    ).get(control_exec_id)

    if control_exec is None:
        raise ValueError("ControlExecution not found")

    action_execs: List[ActionExecution] = await provider.get_repository(
        ActionExecution
    ).get_many(control_exec.action_execution_ids)
    # Get many not in order, so we need to sort it
    action_execs = sorted(action_execs, key=lambda x: x.order)

    action_ids = [a.id for a in action_execs]

    control_info = ControlInfo(
        customer_id=control_exec.customer_id,
        control_id=control_exec.control_id,
        control_execution_id=control_exec.id,
        entity_id=control_exec.entity_id,
        compliance_instruction=control_exec.compliance_instruction,
    )

    return control_exec, control_info, action_ids


def setup_state_persistence(
    control_info: ControlInfo,
) -> SqlStatePersistence:
    """Setup state persistence for the graph execution."""
    persistence = SqlStatePersistence(
        graph_id=str(control_info.control_execution_id),
        connection_string=SQLITE_DATABASE_SYNC_URL,
    )

    return persistence


def setup_agent_messages_for_resume(state: State) -> None:
    if (
        hasattr(state, "agent_messages")
        and len(state.agent_messages) > 0
        and isinstance(state.agent_messages[-1].parts[-1], ToolCallPart)
    ):
        last_agent_message = state.agent_messages[-1]
        # last tool call
        last_tool_call: ToolCallPart = last_agent_message.parts[-1]

        state.agent_messages.append(
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name=last_tool_call.tool_name,
                        content="Please resume the task.",
                        tool_call_id=last_tool_call.tool_call_id,
                    )
                ]
            )
        )


async def clean_up_control_execution(
    provider: RepositoryProvider, control_exec: ControlExecution
) -> None:
    # First, clean up persistence and folder state before updating DB
    try:
        SqlStatePersistence.rerun_inplace(
            graph_id=str(control_exec.id),
            start_index=0,
            connection_string=SQLITE_DATABASE_SYNC_URL,
            overwrite_state={},
        )

        setup_control_execution_folder_for_rerun(
            control_execution_folder=construct_control_execution_folder(
                control_exec.control_id,
                control_exec.entity_id,
                control_exec.id,
            ),
            start_index=0,
        )
    except Exception as e:
        logfire.error(f"Failed to clean up persistence/folder state: {e}")
        raise ValueError(f"Cannot clean up control execution: {e}") from e

    control_exec.reset()
    await provider.get_repository(ControlExecution).update(control_exec)
    action_execs = await provider.get_repository(ActionExecution).get_many(
        control_exec.action_execution_uuids
    )
    for action_exec in action_execs:
        action_exec.reset()
        await provider.get_repository(ActionExecution).update(action_exec)
