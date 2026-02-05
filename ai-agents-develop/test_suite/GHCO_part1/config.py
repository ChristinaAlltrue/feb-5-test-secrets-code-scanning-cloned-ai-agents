"""
Configuration for Custom Questionnaire Assistant test module.
"""

MODULE_CONFIG = {
    "name": "GHCO_part1",
    "description": "File Collection Agent for handling GitHub organization requests",
    "action_prototype": "FileCollectionAgent",
    "schema_module": "app.core.agents.action_prototype.audit_file_collection_agent.schema",
    "schema_class": "FileCollectionAgentDeps",
    "test_settings_module": "test_suite.GHCO_part1.settings",
}
