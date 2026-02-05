from pydantic import Field
from pydantic.dataclasses import dataclass
from pydantic_graph import BaseNode, GraphRunContext

from app.core.agents.action_prototype.github_auditor_with_screenshot.schema import (
    GithubPRAuditorAgentWithScreenshotDeps,
    GithubPRAuditorAgentWithScreenshotOutput,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot.tool import (
    github_pr_auditor_with_screenshot,
)
from app.core.agents.utils.action_lifecycle.pausable_action_lifecycle import (
    PausableActionLifecycleManager,
)
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State

YES = "yes"


@dataclass
class GithubPRAuditorAgentWithScreenshot(BaseNode[State]):
    lifecycle: PausableActionLifecycleManager[
        GithubPRAuditorAgentWithScreenshotDeps, GithubPRAuditorAgentWithScreenshotOutput
    ] = Field(
        default_factory=lambda: PausableActionLifecycleManager(
            deps_type=GithubPRAuditorAgentWithScreenshotDeps,
            action_name="GithubPRAuditorAgentWithScreenshot",
        ),
        exclude=True,
    )

    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        return await self.lifecycle.execute(ctx, self._execute_business_logic)

    async def _execute_business_logic(
        self,
        ctx: GraphRunContext[State, GraphDeps],
        current_deps: GithubPRAuditorAgentWithScreenshotDeps,
    ) -> GithubPRAuditorAgentWithScreenshotOutput:
        if ctx.deps.browser_deps is None:
            ctx.deps.init_browser_deps(allowed_domains=["https://github.com"])
        action_deps = ctx.deps.get_action_deps()
        async with patched_action_deps(ctx, action_deps) as new_ctx:
            result = await github_pr_auditor_with_screenshot(
                new_ctx,
                target_PR=current_deps.target_PR,
                github_token=current_deps.github_token,
                goal=current_deps.goal,
                username=current_deps.username,
                password=current_deps.password,
                mfa_secret=current_deps.mfa_secret,
                pause_enabled=current_deps.pause_enabled,
            )

        return result
