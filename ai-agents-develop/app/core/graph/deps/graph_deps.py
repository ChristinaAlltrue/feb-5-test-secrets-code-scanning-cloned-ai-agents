from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Type, Union
from uuid import UUID

import logfire
from alltrue.agents.schema.control_execution import Edge
from alltrue.agents.schema.customer_credential import CredentialValue
from pydantic import ConfigDict, Field
from pydantic_graph import BaseNode, End, GraphRunContext

from app.core.agents.condition_resolve_agent.condition_resolve_agent import (
    resolve_condition,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.base_deps import BaseDeps, BrowserDeps, ControlInfo
from app.core.graph.state.state import State
from app.exceptions.control_exceptions import ControlExecutionNotFoundException

# Constants
END_NODE_INDEX = -999  # Special index indicating end of graph execution


class GraphDeps(BaseDeps):
    """
    GraphDeps holds all the static/configuration data needed for graph execution.
    This includes data that won't change during the graph execution.
    """

    model_config = ConfigDict(extra="allow")
    # Core graph structure
    nodes: tuple[Type[BaseNode], ...]  # List of nodes to be executed
    edges: list[Edge]  # Edges for the control flow
    edges_by_source: dict = Field(
        default_factory=dict
    )  # Map of edges by source node index

    # Execution state
    node_ind: int  # current node index
    args: List[dict]  # independent variables for each node
    deps: list = Field(default_factory=list)  # Dependencies for each node

    # Metadata
    action_ids: list[UUID]  # IDs of actions to be executed
    control_info: ControlInfo  # Control execution info
    credentials: List[Dict[str, CredentialValue]] = Field(
        default_factory=list
    )  # Credentials for each node

    # Initialization and cleanup methods
    def model_post_init(self, __context):
        """Initialize the edges_by_source map and validate edge bounds"""
        super().model_post_init(__context)
        for edge in self.edges:
            # Validate edge bounds
            if edge.source >= len(self.nodes):
                raise ValueError(f"Edge source out of bounds: {edge.source}")
            if edge.target != -999 and edge.target >= len(self.nodes):
                raise ValueError(f"Edge target out of bounds: {edge.target}")

            # Build edges_by_source map
            if edge.source not in self.edges_by_source:
                self.edges_by_source[edge.source] = []
            self.edges_by_source[edge.source].append(edge)

    async def dispose(self):
        """Clean up resources"""
        if self.browser_deps:
            await self.browser_deps.dispose()

    # Node and edge access methods
    def get_node(self, node_ind: int) -> BaseNode:
        """Get node by index"""
        return self.nodes[node_ind]()

    def get_next_edges(self, node_ind: int) -> List[Edge]:
        """Get edges from a source node index"""
        return self.edges_by_source.get(node_ind, [])

    def is_end_node(self, index: int) -> bool:
        """Check if the given node index represents the end node"""
        return index == END_NODE_INDEX

    def get_deps_for_node(self, node_ind: int) -> dict:
        """Get dependencies for a node"""
        if node_ind < 0 or node_ind >= len(self.deps):
            raise IndexError(f"Invalid node_ind {node_ind}")
        return self.deps[node_ind]

    def get_args_for_node(self, node_ind: int) -> dict:
        """Get arguments for a node"""
        if node_ind < 0 or node_ind >= len(self.args):
            raise IndexError(f"Invalid node_ind {node_ind}")
        return self.args[node_ind]

    def get_browser_deps(self) -> BrowserDeps | None:
        """Get browser state"""
        return self.browser_deps

    # Graph navigation methods
    async def go_to_end_node(self, from_node_ind: int):
        """Set final result and return End node"""
        logfire.info(f"Go to End Node. Last node index: {from_node_ind}")
        await self.set_current_node_index(node_ind=END_NODE_INDEX)
        return End(data=None)

    async def _handle_conditional_edges(
        self, edges: List[Edge], from_node: int
    ) -> BaseNode:
        """Handle navigation through conditional edges"""
        condition_map = {edge.condition: edge.target for edge in edges}
        logfire.info(f"Condition map: {condition_map}")

        if "else" not in condition_map:
            raise Exception("Conditional edges must have an else edge")

        else_node = condition_map["else"]

        # Check each condition
        for condition, target_node_ind in condition_map.items():
            if condition == "else":
                continue

            logfire.info(f"Condition: '{condition}'")
            if await resolve_condition(self.output, condition):
                logfire.info(f"Condition is met. Next node: {target_node_ind}")
                if self.is_end_node(target_node_ind):
                    return await self.go_to_end_node(from_node_ind=from_node)
                else:
                    self.node_ind = target_node_ind
                    return self.get_node(self.node_ind)

        # No condition met; follow the 'else' path
        logfire.info(f"No condition met. Using 'else' edge to node {else_node}")
        if self.is_end_node(else_node):
            return await self.go_to_end_node(from_node_ind=from_node)
        else:
            self.node_ind = else_node
            return self.get_node(self.node_ind)

    def get_next_node_ind(self) -> int:
        """Get the next node index"""
        next_edges = self.get_next_edges(self.node_ind)
        if not next_edges:
            return END_NODE_INDEX
        return next_edges[0].target

    async def get_next_node(self) -> BaseNode:
        """Determine and return the next node in the graph execution"""
        current_node_ind = self.node_ind
        next_edges = self.get_next_edges(current_node_ind)

        # Handle end of graph
        if not next_edges:
            return await self.go_to_end_node(from_node_ind=current_node_ind)

        # Handle simple edge case
        if len(next_edges) == 1:
            target_node_ind = next_edges[0].target
            if self.is_end_node(target_node_ind):
                return await self.go_to_end_node(from_node_ind=current_node_ind)
            else:
                self.node_ind = target_node_ind
                await self.set_current_node_index(node_ind=target_node_ind)
                return self.get_node(self.node_ind)

        # Handle conditional edges
        return await self._handle_conditional_edges(next_edges, current_node_ind)

    async def set_current_node_index(self, node_ind: int) -> None:
        """Set the current node index"""
        control_exec = await self.control_repo.get(
            self.control_info.control_execution_id
        )
        if not control_exec:
            raise ControlExecutionNotFoundException(
                f"ControlExecution with id {self.control_info.control_execution_id} not found"
            )
        control_exec.current_action_index = node_ind
        await self.control_repo.update(control_exec)

    def _recursive_parse_dep_value(
        self, dep: dict, max_depth: int = 100, current_depth: int = 0
    ):
        """
        Parse a dependency value based on its type
        ControlVariableDeps is only Union of PrimitiveDeps, ObjectDeps and ArrayDeps
        """
        if current_depth > max_depth:
            raise ValueError(
                f"Maximum recursion depth ({max_depth}) exceeded while parsing dependency"
            )

        value_type = dep.get("value_type")
        if value_type == "primitive":
            return dep.get("value")
        elif value_type == "array":
            return [
                self._recursive_parse_dep_value(item, max_depth, current_depth + 1)
                for item in dep.get("value", [])
            ]
        elif value_type == "object":
            return {
                key: self._recursive_parse_dep_value(
                    value, max_depth, current_depth + 1
                )
                for key, value in dep.get("value", {}).items()
            }
        else:
            raise ValueError(f"Unsupported value_type '{value_type}' in dep")

    # Dependency resolution
    def get_current_deps(self, output: list[dict]) -> dict:
        """Resolve current node dependencies

        Args:
            output (list[dict]): The output of all the previous actions, use for ref deps

        Returns:
            dict: The resolved dependencies
        """
        resolved = {}
        current_deps = self.get_deps_for_node(self.node_ind)

        for key, dep in current_deps.items():
            value_type = dep.get("value_type")

            if value_type == "primitive":
                resolved[key] = dep.get("value")
            elif value_type == "array" or value_type == "object":
                resolved[key] = self._recursive_parse_dep_value(dep, max_depth=30)
            elif value_type == "ref":
                action_index = dep.get("action_index")
                field = dep.get("field")

                if not isinstance(action_index, int) or action_index >= len(output):
                    raise IndexError(
                        f"Invalid action_index {action_index} for ref dep '{key}'"
                    )

                referenced_output = output[action_index]
                if field not in referenced_output:
                    raise KeyError(
                        f"Field '{field}' not found in output[{action_index}] for ref dep '{key}'"
                    )

                resolved[key] = referenced_output[field]
            elif value_type == "args":
                resolved[key] = self.get_args_for_node(self.node_ind)[key]
            else:
                raise ValueError(f"Unknown value_type '{value_type}' in dep '{key}'")
        return resolved

    # Generate action deps
    def get_action_deps(self, node_ind: int | None = None) -> ActionDeps:
        """
        Generates ActionDeps for a specific node, injecting the action_repo.
        """
        if node_ind is None:
            node_ind = self.node_ind

        return ActionDeps(
            control_info=self.control_info,
            node_ind=node_ind,
            working_dir=self.working_dir,
            action_id=self.action_ids[node_ind],
            action_name=self.nodes[node_ind].__name__,
            action_repo=self.action_repo,
            control_repo=self.control_repo,
            browser_deps=self.browser_deps,
            credentials=self.credentials[node_ind],
        )


@asynccontextmanager
async def patched_action_deps(
    ctx: GraphRunContext[State, Union[GraphDeps, ActionDeps]], new_deps: ActionDeps
) -> AsyncGenerator[GraphRunContext[State, ActionDeps], None]:
    original = ctx.deps
    ctx.deps = new_deps
    try:
        yield ctx
    finally:
        ctx.deps = original
