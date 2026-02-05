"""
Configuration for Gmail Listener test module.
"""

MODULE_CONFIG = {
    "name": "gmail_listener",
    "description": "Gmail Listener agent for analyzing emails and determining if they match specified goals",
    "action_prototype": "GmailListener",
    "schema_module": "app.core.agents.action_prototype.gmail_listener.schema",
    "schema_class": "GmailListenerAgentDeps",
    "test_settings_module": "test_suite.gmail_listener.settings",
}
