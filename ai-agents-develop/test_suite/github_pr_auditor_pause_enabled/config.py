"""
Configuration for GitHub PR Auditor Pause Enabled.
"""

MODULE_CONFIG = {
    "name": "github_pr_auditor_with_pause_enabled",
    "description": "GitHub PR Auditor with Pause capabilities",
    "action_prototype": "GithubPRAuditorWithScreenshot",
    "schema_module": "app.core.agents.action_prototype.github_auditor_with_screenshot.schema",
    "schema_class": "GithubPRAuditorAgentWithScreenshotDeps",
    "test_settings_module": "test_suite.github_pr_auditor_pause_enabled.settings",
}
