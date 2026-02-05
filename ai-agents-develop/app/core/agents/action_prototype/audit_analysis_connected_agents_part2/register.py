from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.action import (
    AuditAnalysisConnectedAgentsPart2,
)
from app.core.agents.action_prototype.audit_analysis_connected_agents_part2.schema import (
    AuditAnalysisConnectedAgentOutputPart2,
    AuditAnalysisConnectedNodeDepsPart2,
)
from app.core.agents.action_prototype.bundles import ActionPrototypeBundle

NODE_NAME = "ProvisioningAuditorManager"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Connects Audit file collection and analysis agents Part 2",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(AuditAnalysisConnectedNodeDepsPart2),
    output_schema=extract_output_schema_from_model(
        AuditAnalysisConnectedAgentOutputPart2
    ),
)

audit_analysis_connected_agent_part2_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=AuditAnalysisConnectedNodeDepsPart2,
    output_model=AuditAnalysisConnectedAgentOutputPart2,
    logic_cls=AuditAnalysisConnectedAgentsPart2,
)
audit_analysis_connected_agent_part2_bundle.register()
