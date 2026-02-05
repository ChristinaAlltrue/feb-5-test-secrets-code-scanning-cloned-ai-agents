"""
Configuration for Custom Questionnaire Assistant test module.
"""

MODULE_CONFIG = {
    "name": "custom_questionnaire_assistant",
    "description": "Custom Questionnaire Assistant agent for filling spreadsheets based on context documents",
    "action_prototype": "CustomQuestionnaireAssistant",
    "schema_module": "app.core.agents.action_prototype.custom_questionnaire_assistant.schema",
    "schema_class": "CustomQuestionnaireAssistantNodeDeps",
    "test_settings_module": "test_suite.custom_questionnaire_assistant.settings",
}
