"""
Configuration for Send Gmail test module.
"""

MODULE_CONFIG = {
    "name": "send_gmail",
    "description": "Send Gmail agent for sending emails based on specified goals",
    "action_prototype": "SendGmail",
    "schema_module": "app.core.agents.action_prototype.send_gmail.schema",
    "schema_class": "SendGmailDeps",
    "test_settings_module": "test_suite.send_gmail.settings",
}
