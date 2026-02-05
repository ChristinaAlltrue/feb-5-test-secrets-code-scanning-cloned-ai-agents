from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.GHCO_auditor.action import GHCOAuditor
from app.core.agents.action_prototype.GHCO_auditor.prompt import PROMPT
from app.core.agents.action_prototype.GHCO_auditor.schema import (
    GHCOAuditorDeps,
    GHCOAuditorOutput,
)

NODE_NAME = "GHCOAuditor"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Prebuilt action to audit the GHCO compliance",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GHCOAuditorDeps),
    output_schema=extract_output_schema_from_model(GHCOAuditorOutput),
    prompt=PROMPT,
)


GHCO_auditor_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GHCOAuditorDeps,
    output_model=GHCOAuditorOutput,
    logic_cls=GHCOAuditor,
)

GHCO_auditor_bundle.register()
