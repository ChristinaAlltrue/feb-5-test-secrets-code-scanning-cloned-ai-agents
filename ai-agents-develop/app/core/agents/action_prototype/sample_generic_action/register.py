from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.sample_generic_action.action import (
    SampleGenericAction,
)
from app.core.agents.action_prototype.sample_generic_action.schema import (
    SampleGenericActionDeps,
    SampleGenericActionOutput,
)

NODE_NAME = "sample_generic_action"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="An Add Number action that adds a number to the input",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(SampleGenericActionDeps),
    output_schema=extract_output_schema_from_model(SampleGenericActionOutput),
)


sample_generic_action_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=SampleGenericActionDeps,
    output_model=SampleGenericActionOutput,
    logic_cls=SampleGenericAction,
)

sample_generic_action_bundle.register()
