from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.audit_analysis_agent.action import (
    AuditAnalysisAgent,
)
from app.core.agents.action_prototype.audit_analysis_agent.schema import (
    AuditAnalysisAgentDeps,
    AuditAnalysisAgentOutput,
)
from app.core.agents.action_prototype.bundles import ActionPrototypeBundle

NODE_NAME = "AuditAnalysisAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Audit Analysis Agent that processes files and generates comprehensive audit reports with control testing and risk assessment",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(AuditAnalysisAgentDeps),
    output_schema=extract_output_schema_from_model(AuditAnalysisAgentOutput),
    prompt="Audit Analysis Agent that processes uploaded files to generate comprehensive audit reports",
)


audit_analysis_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=AuditAnalysisAgentDeps,
    output_model=AuditAnalysisAgentOutput,
    logic_cls=AuditAnalysisAgent,
)

audit_analysis_agent_bundle.register()
