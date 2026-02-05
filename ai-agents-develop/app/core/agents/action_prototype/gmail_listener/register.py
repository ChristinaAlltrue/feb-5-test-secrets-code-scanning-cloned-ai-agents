from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.gmail_listener.action import GmailListenerAgent
from app.core.agents.action_prototype.gmail_listener.prompt import GMAIL_LISTENER_PROMPT
from app.core.agents.action_prototype.gmail_listener.schema import (
    GmailListenerAgentDeps,
    GmailListenerAgentOutput,
)

NODE_NAME = "GmailListener"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Run the Gmail listener agent to check if emails match the specified goal",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(GmailListenerAgentDeps),
    output_schema=extract_output_schema_from_model(GmailListenerAgentOutput),
    prompt=GMAIL_LISTENER_PROMPT,
)


gmail_listener_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=GmailListenerAgentDeps,
    output_model=GmailListenerAgentOutput,
    logic_cls=GmailListenerAgent,
)

gmail_listener_bundle.register()
