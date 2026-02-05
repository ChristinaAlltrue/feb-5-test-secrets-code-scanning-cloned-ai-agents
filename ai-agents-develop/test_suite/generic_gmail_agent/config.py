"""
Configuration for Generic Gmail Agent test module.
"""

MODULE_CONFIG = {
    "name": "generic_gmail_agent",
    "description": "Run a generic Gmail agent via MCP to perform Gmail operations",
    "action_prototype": "generic_gmail_agent",
    "schema_module": "app.core.agents.action_prototype.generic_gmail_agent.schema",
    "schema_class": "GenericGmailAgentDeps",
    "test_settings_module": "test_suite.generic_gmail_agent.settings",
}
