from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.pause.action import Pause

NODE_NAME = "pause"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Pause the execution and wait for user to provide more info to resume",
    category=AgentActionCategory.TOOLS,
    deps_schema=None,
    output_schema=None,
)

pause_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=None,
    output_model=None,
    logic_cls=Pause,
)
pause_bundle.register()
