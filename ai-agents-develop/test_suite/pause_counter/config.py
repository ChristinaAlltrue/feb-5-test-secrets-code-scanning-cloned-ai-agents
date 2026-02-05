"""
Configuration for GitHub PR Auditor Pause Enabled.
"""

MODULE_CONFIG = {
    "name": "Counter to Zero with Pause",
    "description": "Counter with pause enabled until it reaches zero",
    "action_prototype": "Counter",
    "schema_module": "app.core.agents.action_prototype.counter.schema",
    "schema_class": "Start",
    "test_settings_module": "test_suite.pause_counter.settings",
}
