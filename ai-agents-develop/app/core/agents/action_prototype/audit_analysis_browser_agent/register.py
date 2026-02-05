from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.audit_analysis_browser_agent.action import (
    AuditAnalysisBrowserAgent,
)
from app.core.agents.action_prototype.audit_analysis_browser_agent.schema import (
    AuditAnalysisBrowserAgentDeps,
    AuditAnalysisBrowserAgentOutput,
)
from app.core.agents.action_prototype.bundles import ActionPrototypeBundle

NODE_NAME = "AuditAnalysisBrowserAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Audit Analysis Browser Agent - Web automation and file downloads for audit processes using Playwright",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(AuditAnalysisBrowserAgentDeps),
    output_schema=extract_output_schema_from_model(AuditAnalysisBrowserAgentOutput),
    prompt="Audit Analysis Browser Agent that automates web navigation and file downloads for audit processes",
)


audit_analysis_browser_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=AuditAnalysisBrowserAgentDeps,
    output_model=AuditAnalysisBrowserAgentOutput,
    logic_cls=AuditAnalysisBrowserAgent,
)

audit_analysis_browser_agent_bundle.register()
