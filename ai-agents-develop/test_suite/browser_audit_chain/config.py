"""
Configuration for Browser + Audit Analysis Chain test module.
"""

MODULE_CONFIG = {
    "name": "browser_audit_chain",
    "description": "Chain Audit Analysis Browser Agent with Audit Analysis Agent for end-to-end workflow",
    "control_type": "Multiple Actions",
    "test_settings_module": "test_suite.browser_audit_chain.settings",
    "action_prototype": "AuditAnalysisBrowserAgent",
}
