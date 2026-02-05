from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle, ToolBundle
from app.core.agents.action_prototype.longterm_memory_agent.action import (
    LongtermMemoryAgent,
)
from app.core.agents.action_prototype.longterm_memory_agent.schema import (
    LongtermMemoryAgentDeps,
    LongtermMemoryAgentOutput,
    LongtermMemoryAgentToolParams,
)
from app.core.agents.action_prototype.longterm_memory_agent.tool import (
    longterm_memory_search_tool,
)

NODE_NAME = "longterm_memory_agent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Query the longterm memory system to answer questions based on stored documents",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(LongtermMemoryAgentDeps),
    output_schema=extract_output_schema_from_model(LongtermMemoryAgentOutput),
)


longterm_memory_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=LongtermMemoryAgentDeps,
    output_model=LongtermMemoryAgentOutput,
    logic_cls=LongtermMemoryAgent,
)

longterm_memory_agent_bundle.register()

# =====Register Tool =====
TOOL_ID = longterm_memory_search_tool.__name__
TOOL_DISPLAY_NAME = "Longterm Memory Search"
TOOL_DESCRIPTION = "Query the longterm memory system to answer questions based on stored documents using intelligent search and retrieval."

longterm_memory_tool_bundle = ToolBundle.from_function(
    longterm_memory_search_tool,
    tool_id=TOOL_ID,
    tool_display_name=TOOL_DISPLAY_NAME,
    description=TOOL_DESCRIPTION,
    parameters_model=LongtermMemoryAgentToolParams,
    takes_ctx=True,
    max_retries=10,
    default_model="GPT-5.1 Instant",
)

longterm_memory_tool_bundle.register()
