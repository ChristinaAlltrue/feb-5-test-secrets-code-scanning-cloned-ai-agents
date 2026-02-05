from typing import Dict, List, cast
from uuid import UUID

import logfire
from alltrue.agents.schema.customer_credential import CredentialValue
from pydantic_graph import BaseNode, End, Graph
from pydantic_graph.persistence.file import FileStatePersistence

from app.core.agents.action_prototype.pause.action import Pause
from app.core.graph.deps.graph_deps import GraphDeps
from app.core.graph.run.post_execution import post_process_graph
from app.core.graph.run.utils import (
    clean_up_control_execution,
    create_graph,
    setup_agent_messages_for_resume,
    setup_control_execution,
    setup_state_persistence,
)
from app.core.graph.state.state import State
from app.core.models.models import ActionExecution, ControlExecution
from app.core.storage_dependencies.storage_dependencies import get_provider
from app.exceptions.control_exceptions import (
    GraphExecutionActionRequiredException,
    GraphExecutionRemediationRequiredException,
)


@logfire.instrument()
async def run_graph(
    nodes: tuple[BaseNode],
    action_deps_list: list,
    control_exec_id: UUID,
    credentials: List[Dict[str, CredentialValue]],
    step_by_step: bool = False,
    allow_rerun: bool = False,
) -> State:
    """Execute a graph of nodes with the given dependencies.
    1. setup control execution
    2. create graph
    3. setup state persistence
    4. load previous state if exists
    5. create GraphDeps instance with static configuration
    6. execute the graph
    7. once the graph execution is complete, do the post processing

    Args:
        nodes: Tuple of nodes to execute
        action_deps_list: List of dependencies
        control_exec_id: UUID of the control execution
        step_by_step: bool = False,
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

        node: BaseNode
        state: State

        # 4. load previous state if exists
        snapshots = await persistence.load_all()

        if not snapshots:
            # No previous state, start fresh
            logfire.info("Starting fresh - no previous snapshots.")
            node = nodes[0]()
            state = State()
            state.manual_init(len(nodes))
        else:
            # Resume from the last snapshot
            last_snapshot = snapshots[-1]
            # If last node was End, we've completed - start fresh
            if isinstance(last_snapshot.node, End):
                if not allow_rerun:
                    raise ValueError("Previous execution completed, cannot rerun.")
                logfire.warning("Starting fresh - previous execution completed.")
                await clean_up_control_execution(async_provider, control_exec)
                node = nodes[0]()
                state = State()
                state.manual_init(len(nodes))
            else:
                # Resume from last snapshot
                state = cast(State, last_snapshot.state)
                node = cast(BaseNode, last_snapshot.node)
                setup_agent_messages_for_resume(state)

                # If rerun from the middle, the last snapshot status is created or error,
                # so we need to delete it to avoid duplicates and ensure correct sequence
                if getattr(last_snapshot, "status", None) in {"created", "error"}:
                    await persistence.delete_latest_snapshot()

        # 5. create GraphDeps instance with static configuration
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

        try:
            control_exec.mark_in_progress()
            await async_provider.get_repository(ControlExecution).update(control_exec)
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
            return state

        except GraphExecutionActionRequiredException as e:
            logfire.warning(
                f"Graph execution action required, suspending execution at {control_exec.current_action_index}"
            )
            return state

        except GraphExecutionRemediationRequiredException as e:
            logfire.warning(
                f"Graph execution remediation required, suspending execution at {control_exec.current_action_index}"
            )
            return state

        except Exception as e:
            logfire.error(f"Error in graph execution: {e}")
            raise
        finally:
            logfire.info("Disposing of deps")
            await graph_deps.dispose()  # Clean up browser deps through deps

        return state


class SuspendExecution(Exception):
    """Stop the execution of the graph."""


async def execute_graph(
    graph: Graph,
    node: BaseNode,
    state: State,
    deps: GraphDeps,
    persistence: FileStatePersistence,
    control_exec: ControlExecution,
    step_by_step: bool = False,
) -> BaseNode:
    """Execute the graph with the given node, state and deps."""
    async with graph.iter(node, state=state, deps=deps, persistence=persistence) as run:
        while True:
            try:
                control_exec.add_log(f"Executing node: {node.__class__.__name__}")

                next_node = await run.next(node)
                control_exec.add_action_exec_history(state.node_ind)
                control_exec.add_log(
                    f"Completed execution of node: {node.__class__.__name__}"
                )
                control_exec.add_log(f"Next node: {next_node.__class__.__name__}")
                await deps.control_repo.update(control_exec)

                if isinstance(next_node, End):
                    break

                if isinstance(next_node, Pause):
                    control_exec.mark_action_required("Graph execution Paused")
                    control_exec.add_log("Graph execution Paused")
                    await deps.control_repo.update(control_exec)
                    break

                node = next_node
                # if step by step, raise SuspendExecution to suspend the execution
                if step_by_step:
                    raise SuspendExecution()

            except GraphExecutionActionRequiredException as e:
                control_exec.mark_action_required(str(e))
                await deps.control_repo.update(control_exec)
                raise

            except GraphExecutionRemediationRequiredException as e:
                control_exec.mark_remediation_required(str(e))
                await deps.control_repo.update(control_exec)
                raise

            except SuspendExecution:
                logfire.warning("Suspend execution of the graph")
                control_exec.mark_action_required("Awaiting next step")
                await deps.control_repo.update(control_exec)
                raise

            except Exception as node_error:
                error_msg = f"Failed executing node {node.__class__.__name__}: {str(node_error)}"
                control_exec.add_log(error_msg)
                await deps.control_repo.update(control_exec)
                logfire.error(error_msg)
                raise

        if next_node and isinstance(next_node, Pause):
            logfire.info("Graph paused, saving state for later resumption")
            return next_node

        if next_node and isinstance(next_node, End):
            logfire.info("Reached the end of the graph")
            return next_node

        raise ValueError("Graph did not reach a terminal state.")
