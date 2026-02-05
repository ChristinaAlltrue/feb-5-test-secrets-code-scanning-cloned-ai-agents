"""
Configuration for audit_analysis_connected_agents test module.
"""

MODULE_CONFIG = {
    "name": "audit_analysis_connected_agents",
    "description": "GHCO Connected Agent for handling GitHub organization requests",
    "action_prototype": "AuditorManager",
    "schema_module": "app.core.agents.action_prototype.audit_analysis_connected_agents.schema",
    "schema_class": "AuditAnalysisConnectedNodeDeps",
    "test_settings_module": "test_suite.audit_analysis_connected_agents.settings",
}
