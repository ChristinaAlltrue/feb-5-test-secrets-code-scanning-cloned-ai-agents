"""
Configuration for Supervisor Agent test module.
"""

MODULE_CONFIG = {
    "name": "supervisorAgent",
    "description": "Supervisor agent orchestrating one tool to complete a task",
    "action_prototype": "SupervisorAgent",
    "schema_module": "app.core.agents.action_prototype.supervisor_agent.schema",
    "schema_class": "SupervisorAgentDeps",
    "test_settings_module": "test_suite.supervisor_agent.settings",
}
