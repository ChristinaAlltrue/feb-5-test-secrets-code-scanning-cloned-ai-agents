from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.generic_auditor_agent.action import (
    GenericAuditorAgent,
)
from app.core.agents.action_prototype.generic_auditor_agent.prompt import PROMPT
from app.core.agents.action_prototype.generic_auditor_agent.schema import (
    GenericAuditorAgentDeps,
    GenericAuditorAgentOutput,
)

NODE_NAME = "GenericAuditorAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="run the Web supervisor agent, which can handle login, screenshot, navigation on the website and file download and check",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GenericAuditorAgentDeps),
    output_schema=extract_output_schema_from_model(GenericAuditorAgentOutput),
    prompt=PROMPT,
)


generic_auditor_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GenericAuditorAgentDeps,
    output_model=GenericAuditorAgentOutput,
    logic_cls=GenericAuditorAgent,
)

generic_auditor_agent_bundle.register()
