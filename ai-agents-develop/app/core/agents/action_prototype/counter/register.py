from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.counter.action import Counter
from app.core.agents.action_prototype.counter.schema import Output, Start

NODE_NAME = "Counter"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Counter to zero with pause enabled",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(Start),
    output_schema=extract_output_schema_from_model(Output),
    prompt="",
)


counter_listener_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=Start,
    output_model=Output,
    logic_cls=Counter,
)

counter_listener_bundle.register()
