from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.custom_questionnaire_assistant_v2.action import (
    CustomQuestionnaireAssistantV2,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant_v2.prompt import (
    CUSTOM_QUESTIONNAIRE_ASSISTANT_V2_PROMPT,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant_v2.schema import (
    CustomQuestionnaireAssistantV2NodeDeps,
    CustomQuestionnaireAssistantV2Output,
)

NODE_NAME = "CustomQuestionnaireAssistantV2"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="CustomQuestionnaireAssistant agent to fill in the spreadsheet based on the context document",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(CustomQuestionnaireAssistantV2NodeDeps),
    output_schema=extract_output_schema_from_model(
        CustomQuestionnaireAssistantV2Output
    ),
    prompt=CUSTOM_QUESTIONNAIRE_ASSISTANT_V2_PROMPT,
)


custom_questionnaire_assistant_v2_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=CustomQuestionnaireAssistantV2NodeDeps,
    output_model=CustomQuestionnaireAssistantV2Output,
    logic_cls=CustomQuestionnaireAssistantV2,
)

custom_questionnaire_assistant_v2_bundle.register()
