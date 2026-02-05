from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.audit_analysis_connected_agents.action import (
    AuditAnalysisConnectedAgents,
)
from app.core.agents.action_prototype.audit_analysis_connected_agents.schema import (
    AuditAnalysisConnectedAgentOutput,
    AuditAnalysisConnectedNodeDeps,
)
from app.core.agents.action_prototype.bundles import ActionPrototypeBundle

NODE_NAME = "AuditorManager"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Connects Audit file collection and analysis agents",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(AuditAnalysisConnectedNodeDeps),
    output_schema=extract_output_schema_from_model(AuditAnalysisConnectedAgentOutput),
)

audit_analysis_connected_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=AuditAnalysisConnectedNodeDeps,
    output_model=AuditAnalysisConnectedAgentOutput,
    logic_cls=AuditAnalysisConnectedAgents,
)
audit_analysis_connected_agent_bundle.register()
