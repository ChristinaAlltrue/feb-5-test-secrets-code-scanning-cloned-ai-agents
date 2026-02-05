"""
To load the action prototypes and tools, we use a registry pattern.
This allows us to dynamically register and retrieve action prototypes and tools by name.
You must manually import the module in "app/core/prototype_loader.py" to ensure the registration happens.
"""

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from app.core.agents.action_prototype.bundles import (
        ActionPrototypeBundle,
        ToolBundle,
    )


PROTOTYPE_REGISTRY: Dict[str, "ActionPrototypeBundle"] = {}


def register_prototype(name: str, prototype_bundle: "ActionPrototypeBundle"):
    if name in PROTOTYPE_REGISTRY:
        raise ValueError(f"Prototype '{name}' already registered.")
    PROTOTYPE_REGISTRY[name] = prototype_bundle


GRAPH_NODE_REGISTRY = {}


def register_action(name, action):
    if name in GRAPH_NODE_REGISTRY:
        raise ValueError(f"Action '{name}' already registered.")
    GRAPH_NODE_REGISTRY[name] = action


# ===== Tools Registry =====
TOOLS_REGISTRY: Dict[str, "ToolBundle"] = {}


def register_tool(tool_id: str, tool_bundle: "ToolBundle"):
    if tool_id in TOOLS_REGISTRY:
        raise ValueError(f"Tool '{tool_id}' already registered.")
    TOOLS_REGISTRY[tool_id] = tool_bundle


def ensure_registry_loaded():
    """
    The worker is different from the api service process, we need to initialize the registry in the worker process.
    """
    global TOOLS_REGISTRY
    global PROTOTYPE_REGISTRY
    global GRAPH_NODE_REGISTRY
    if not TOOLS_REGISTRY or not PROTOTYPE_REGISTRY or not GRAPH_NODE_REGISTRY:
        from importlib import import_module

        import_module("app.core.prototype_loader")
