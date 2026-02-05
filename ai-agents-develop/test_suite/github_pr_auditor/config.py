"""
Configuration for GitHub PR Auditor test module.
"""

MODULE_CONFIG = {
    "name": "github_pr_auditor",
    "description": "GitHub PR Auditor without screenshots",
    "action_prototype": "GithubPRAuditor",
    "schema_module": "app.core.agents.action_prototype.github_auditor.schema",
    "schema_class": "GithubPRAuditorAgentDeps",
    "test_settings_module": "test_suite.github_pr_auditor.settings",
}
