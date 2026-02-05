from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.screenshot.action import ScreenshotAgent
from app.core.agents.action_prototype.screenshot.schema import (
    ScreenshotDeps,
    ScreenshotOutput,
)

NODE_NAME = "Screenshot"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.BROWSER,
    description="run the screenshot agent",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(ScreenshotDeps),
    output_schema=extract_output_schema_from_model(ScreenshotOutput),
)


github_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=ScreenshotDeps,
    output_model=ScreenshotOutput,
    logic_cls=ScreenshotAgent,
)

github_bundle.register()
