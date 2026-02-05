from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.github_auditor_with_screenshot.action import (
    GithubPRAuditorAgentWithScreenshot,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot.prompt import (
    PROMPT,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot.schema import (
    GithubPRAuditorAgentWithScreenshotDeps,
    GithubPRAuditorAgentWithScreenshotOutput,
    GithubPRAuditorAgentWithScreenshotPauseOutput,
)

NODE_NAME = "GithubPRAuditorWithScreenshot"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Run the github PR auditor agent to check if the PR is passed the check",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GithubPRAuditorAgentWithScreenshotDeps),
    output_schema=extract_output_schema_from_model(
        GithubPRAuditorAgentWithScreenshotOutput
    ),
    prompt=PROMPT,
)


github_pr_auditor_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GithubPRAuditorAgentWithScreenshotDeps,
    output_model=GithubPRAuditorAgentWithScreenshotOutput
    | GithubPRAuditorAgentWithScreenshotPauseOutput,
    logic_cls=GithubPRAuditorAgentWithScreenshot,
)

github_pr_auditor_bundle.register()
