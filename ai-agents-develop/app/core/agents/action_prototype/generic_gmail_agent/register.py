from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle, ToolBundle
from app.core.agents.action_prototype.generic_gmail_agent.action import (
    GenericGmailAgent,
)
from app.core.agents.action_prototype.generic_gmail_agent.schema import (
    GenericGmailAgentDeps,
    GenericGmailAgentOutput,
    GenericGmailAgentToolParams,
)
from app.core.agents.action_prototype.generic_gmail_agent.tool import (
    generic_gmail_agent_tool,
)

NODE_NAME = "generic_gmail_agent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Run a generic Gmail agent via MCP to perform Gmail operations",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GenericGmailAgentDeps),
    output_schema=extract_output_schema_from_model(GenericGmailAgentOutput),
)


generic_gmail_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GenericGmailAgentDeps,
    output_model=GenericGmailAgentOutput,
    logic_cls=GenericGmailAgent,
)

generic_gmail_agent_bundle.register()

# =====Register Tool =====
TOOL_ID = generic_gmail_agent_tool.__name__
TOOL_DISPLAY_NAME = "Gmail MCP"
TOOL_DESCRIPTION = "Gmail MCP lets AI Agents connect directly to your Gmail Account. It helps them read, write, and organize emails."

gmail_tool_bundle = ToolBundle.from_function(
    generic_gmail_agent_tool,
    tool_id=TOOL_ID,
    tool_display_name=TOOL_DISPLAY_NAME,
    description=TOOL_DESCRIPTION,
    parameters_model=GenericGmailAgentToolParams,
    takes_ctx=True,
    max_retries=10,
    default_model="GPT-5.1 Instant",
)

gmail_tool_bundle.register()
