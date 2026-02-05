from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.file_inspection.action import (  # noqa: F401
    FileInspection,
)
from app.core.agents.action_prototype.file_inspection.schema import (
    FileInspectionDeps,
    FileInspectionOutput,
)

NODE_NAME = "FileInspection"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.BROWSER,
    description="Compare the two sheets and return the differences",
    category=AgentActionCategory.TOOLS,
    deps_schema=extract_deps_schema_from_model(FileInspectionDeps),
    output_schema=extract_output_schema_from_model(FileInspectionOutput),
)


file_inspection_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=FileInspectionDeps,
    output_model=FileInspectionOutput,
    logic_cls=FileInspection,
)

file_inspection_bundle.register()
