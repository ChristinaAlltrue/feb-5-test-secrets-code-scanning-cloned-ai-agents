"""
Configuration for GHCO Auditor test module.
"""

MODULE_CONFIG = {
    "name": "ghco_auditor",
    "description": "GHCO Auditor for compliance checking",
    "action_prototype": "GHCOAuditor",
    "schema_module": "app.core.agents.action_prototype.GHCO_auditor.schema",
    "schema_class": "GHCOAuditorDeps",
    "test_settings_module": "test_suite.ghco_auditor.settings",
}
