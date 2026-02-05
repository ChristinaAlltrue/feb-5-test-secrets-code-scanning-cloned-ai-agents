from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.audit_file_collection_agent.action import (
    FileCollectionAgent,
)
from app.core.agents.action_prototype.audit_file_collection_agent.prompt import (
    FILE_COLLECTION_AGENT_PROMPT,
)
from app.core.agents.action_prototype.audit_file_collection_agent.schema import (
    FileCollectionAgentNodeDeps,
    FileCollectionAgentOutput,
)
from app.core.agents.action_prototype.bundles import ActionPrototypeBundle

NODE_NAME = "FileCollectionAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="Creates audit requests for multiple software applications, waits for BU file submissions, and downloads files when available",
    category=AgentActionCategory.PREBUILT,
    deps_schema=extract_deps_schema_from_model(FileCollectionAgentNodeDeps),
    output_schema=extract_output_schema_from_model(FileCollectionAgentOutput),
    prompt=FILE_COLLECTION_AGENT_PROMPT,
)

audit_file_collection_agent_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=FileCollectionAgentNodeDeps,
    output_model=FileCollectionAgentOutput,
    logic_cls=FileCollectionAgent,
)
audit_file_collection_agent_bundle.register()
