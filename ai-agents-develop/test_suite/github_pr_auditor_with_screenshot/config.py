"""
Configuration for GitHub PR Auditor with Screenshot test module.
"""

MODULE_CONFIG = {
    "name": "github_pr_auditor_with_screenshot",
    "description": "GitHub PR Auditor with screenshot capabilities",
    "action_prototype": "GithubPRAuditorWithScreenshot",
    "schema_module": "app.core.agents.action_prototype.github_auditor_with_screenshot.schema",
    "schema_class": "GithubPRAuditorAgentWithScreenshotDeps",
    "test_settings_module": "test_suite.github_pr_auditor_with_screenshot.settings",
}
