from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.sample.action import Sample
from app.core.agents.action_prototype.sample.schema import SampleDeps, SampleOutput

NODE_NAME = "sample"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="plus 1 to the input",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(SampleDeps),
    output_schema=extract_output_schema_from_model(SampleOutput),
)


sample_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=SampleDeps,
    output_model=SampleOutput,
    logic_cls=Sample,
)

sample_bundle.register()
