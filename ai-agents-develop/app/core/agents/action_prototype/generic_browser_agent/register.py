from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.generic_browser_agent.action import (
    GenericBrowserAgent,
)
from app.core.agents.action_prototype.generic_browser_agent.schema import (
    GenericBrowserAgentActionOutput,
    GenericBrowserAgentDeps,
)

NODE_NAME = "GenericBrowserAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Generic browser agent that can execute any browser-based task including web navigation, data extraction, and file downloads",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GenericBrowserAgentDeps),
    output_schema=extract_output_schema_from_model(GenericBrowserAgentActionOutput),
    prompt=None,
)


generic_browser_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GenericBrowserAgentDeps,
    output_model=GenericBrowserAgentActionOutput,
    logic_cls=GenericBrowserAgent,
)

generic_browser_agent_bundle.register()
