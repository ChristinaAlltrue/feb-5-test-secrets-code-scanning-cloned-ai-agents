"""
Configuration for Custom Questionnaire AssistantV2 test module.
"""

MODULE_CONFIG = {
    "name": "custom_questionnaire_assistant_v2",
    "description": "Custom Questionnaire Assistant agent for filling spreadsheets based on context documents",
    "action_prototype": "CustomQuestionnaireAssistantV2",
    "schema_module": "app.core.agents.action_prototype.custom_questionnaire_assistant_v2.schema",
    "schema_class": "CustomQuestionnaireAssistantV2NodeDeps",
    "test_settings_module": "test_suite.custom_questionnaire_assistant_v2.settings",
}
