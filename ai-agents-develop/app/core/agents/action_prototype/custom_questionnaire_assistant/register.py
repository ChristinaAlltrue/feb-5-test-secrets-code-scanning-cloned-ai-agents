from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.custom_questionnaire_assistant.action import (
    CustomQuestionnaireAssistant,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant.prompt import (
    CUSTOM_QUESTIONNAIRE_ASSISTANT_PROMPT,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant.schema import (
    CustomQuestionnaireAssistantNodeDeps,
    CustomQuestionnaireAssistantOutput,
)

NODE_NAME = "CustomQuestionnaireAssistant"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="CustomQuestionnaireAssistant agent to fill in the spreadsheet based on the context document",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(CustomQuestionnaireAssistantNodeDeps),
    output_schema=extract_output_schema_from_model(CustomQuestionnaireAssistantOutput),
    prompt=CUSTOM_QUESTIONNAIRE_ASSISTANT_PROMPT,
)


custom_questionnaire_assistant_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=CustomQuestionnaireAssistantNodeDeps,
    output_model=CustomQuestionnaireAssistantOutput,
    logic_cls=CustomQuestionnaireAssistant,
)

custom_questionnaire_assistant_bundle.register()
