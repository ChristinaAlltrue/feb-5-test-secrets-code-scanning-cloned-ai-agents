from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.github_auditor.action import GithubPRAuditorAgent
from app.core.agents.action_prototype.github_auditor.prompt import PROMPT
from app.core.agents.action_prototype.github_auditor.schema import (
    GithubPRAuditorAgentDeps,
    GithubPRAuditorAgentOutput,
)

NODE_NAME = "GithubPRAuditor"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Run the github PR auditor agent to check if the PR is passed the check",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GithubPRAuditorAgentDeps),
    output_schema=extract_output_schema_from_model(GithubPRAuditorAgentOutput),
    prompt=PROMPT,
)


github_pr_auditor_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GithubPRAuditorAgentDeps,
    output_model=GithubPRAuditorAgentOutput,
    logic_cls=GithubPRAuditorAgent,
)

github_pr_auditor_bundle.register()
