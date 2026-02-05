from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.start.action import Start
from app.core.agents.action_prototype.start.schema import StartDeps, StartOutput

NODE_NAME = "START"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Start of the control",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(StartDeps),
    output_schema=extract_output_schema_from_model(StartOutput),
)


start_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=StartDeps,
    output_model=StartOutput,
    logic_cls=Start,
)

start_bundle.register()
