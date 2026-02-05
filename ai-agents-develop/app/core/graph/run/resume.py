from typing import Dict, List, cast
from uuid import UUID

import logfire
from alltrue.agents.schema.customer_credential import CredentialValue
from pydantic_graph import BaseNode, End

from app.core.agents.base_node.base_node import AgentBaseNode
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.run.post_execution import post_process_graph
from app.core.graph.run.run import SuspendExecution, execute_graph
from app.core.graph.run.utils import (
    create_graph,
    setup_agent_messages_for_resume,
    setup_control_execution,
    setup_state_persistence,
)
from app.core.graph.state.state import State
from app.core.models.models import ActionExecution, ControlExecution
from app.core.storage_dependencies.storage_dependencies import get_provider


@logfire.instrument()
async def resume_graph(
    nodes: tuple[BaseNode],
    action_deps_list: list,
    control_exec_id: UUID,
    extra_instructions: str,
    credentials: List[Dict[str, CredentialValue]],
    step_by_step: bool = False,
) -> State:
    """Execute a graph of nodes with the given dependencies.
    1. setup control execution
    2. create graph
    3. setup state persistence
    4. create GraphDeps instance with static configuration
    5. load previous state if exists
    6. execute the graph
    7. once the graph execution is complete, do the post processing

    Args:
        nodes: Tuple of nodes to execute
        action_deps_list: List of dependencies
        control_exec_id: UUID of the control execution
        extra_instructions: str,
        step_by_step: bool = False,
        credentials: List of per-node credential dictionaries
    Returns:
        State object containing the final result

    Raises:
        ValueError: If control execution is not found or state directory cannot be created
    """
    async with get_provider() as async_provider:
        # 1. setup control execution
        control_exec, control_info, action_ids = await setup_control_execution(
            async_provider, control_exec_id
        )
        entity_exec_args = control_exec.entity_exec_args

        # 2. create graph
        graph = create_graph(nodes)

        # 3. setup state persistence
        persistence = setup_state_persistence(control_info)

        persistence.set_graph_types(graph)

        # 4. create GraphDeps instance with static configuration
        logfire.info(
            f"Control Execution started from action index: {control_exec.current_action_index}"
        )
        graph_deps = GraphDeps(
            node_ind=control_exec.current_action_index,
            control_info=control_info,
            action_repo=async_provider.get_repository(ActionExecution),
            control_repo=async_provider.get_repository(ControlExecution),
            args=entity_exec_args,
            nodes=nodes,
            action_ids=action_ids,
            edges=control_exec.edges,
            deps=action_deps_list,
            credentials=credentials,
        )

        node: BaseNode
        state: State

        # 5. load previous state, raise error if no previous state is found
        snapshots = await persistence.load_all()
        if not snapshots:
            await graph_deps.dispose()
            raise ValueError("No previous state found, cannot resume graph.")

        # Resume from the last snapshot
        last_snapshot = snapshots[-1]
        state = cast(State, last_snapshot.state)
        setup_agent_messages_for_resume(state)
        node = cast(BaseNode, last_snapshot.node)
        if isinstance(last_snapshot.node, End):
            await graph_deps.dispose()
            raise ValueError("Graph already completed, cannot resume again.")

        if isinstance(node, AgentBaseNode):
            node.extra_instructions = extra_instructions
        else:
            logfire.warning(
                f"Node {node.__class__.__name__} is not an AgentBaseNode, resume graph without extra instructions"
            )

        control_exec.mark_in_progress()
        await async_provider.get_repository(ControlExecution).update(control_exec)

        try:
            # 6. execute the graph
            graph_state = await execute_graph(
                graph=graph,
                node=node,
                state=state,
                deps=graph_deps,
                persistence=persistence,
                control_exec=control_exec,
                step_by_step=step_by_step,
            )
            # 7. once the graph execution is complete, do the post processing
            await post_process_graph(
                graph_state=graph_state,
                state=state,
                control_exec=control_exec,
                control_exec_id=control_exec_id,
                control_info=control_info,
                async_provider=async_provider,
            )
        except SuspendExecution:
            logfire.info("Suspend execution of the graph")
            control_exec.mark_action_required("Awaiting next step")
            await async_provider.get_repository(ControlExecution).update(control_exec)
            return state

        except Exception as e:
            logfire.error(f"Error in graph execution: {e}")
            raise
        finally:
            logfire.info("Disposing of deps")
            await graph_deps.dispose()  # Clean up browser deps through deps

        return state
