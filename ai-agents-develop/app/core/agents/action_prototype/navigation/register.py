from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.navigation.action import Navigation
from app.core.agents.action_prototype.navigation.schema import (
    NavigationDeps,
    NavigationOutput,
)

NODE_NAME = "navigation"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.BROWSER,
    description="Navigate to a URL and perform actions based on human instructions",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(NavigationDeps),
    output_schema=extract_output_schema_from_model(NavigationOutput),
)


navigation_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=NavigationDeps,
    output_model=NavigationOutput,
    logic_cls=Navigation,
)

navigation_bundle.register()
