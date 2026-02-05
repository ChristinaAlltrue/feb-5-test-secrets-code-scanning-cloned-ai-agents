from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.login.action import LoginAgent
from app.core.agents.action_prototype.login.schema import LoginDeps, LoginOutput

NODE_NAME = "login"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.BROWSER,
    description="Login to a website",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(LoginDeps),
    output_schema=extract_output_schema_from_model(LoginOutput),
)


login_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=LoginDeps,
    output_model=LoginOutput,
    logic_cls=LoginAgent,
)

login_bundle.register()
