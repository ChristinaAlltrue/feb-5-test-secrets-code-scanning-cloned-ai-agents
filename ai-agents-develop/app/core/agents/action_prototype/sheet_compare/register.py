from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.sheet_compare.action import (  # noqa: F401
    SheetCompare,
)
from app.core.agents.action_prototype.sheet_compare.schema import (
    SheetCompareDeps,
    SheetCompareOutput,
)

NODE_NAME = "SheetCompare"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.CODE_EXECUTION,
    description="Compare the two sheets and return the differences",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(SheetCompareDeps),
    output_schema=extract_output_schema_from_model(SheetCompareOutput),
)


sheet_compare_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=SheetCompareDeps,
    output_model=SheetCompareOutput,
    logic_cls=SheetCompare,
)

sheet_compare_bundle.register()
