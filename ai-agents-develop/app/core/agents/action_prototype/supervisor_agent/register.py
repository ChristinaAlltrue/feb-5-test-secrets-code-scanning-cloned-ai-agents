from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    ActionType,
    AgentActionCategory,
    extract_deps_schema_from_model,
    extract_output_schema_from_model,
)

from app.core.agents.action_prototype.bundles import ActionPrototypeBundle
from app.core.agents.action_prototype.supervisor_agent.action import Supervisor
from app.core.agents.action_prototype.supervisor_agent.schema import (
    SupervisorAgentDeps,
    SupervisorOutput,
)

NODE_NAME = "SupervisorAgent"

prototype = ActionPrototype(
    name=NODE_NAME,
    type=ActionType.GENERAL,
    description="""A Supervisor Agent is responsible for overseeing and coordinating the actions of other agents within a system.
    It monitors their performance, ensures tasks are executed correctly, and enforces policies or goals.
    The agent acts as a controller that manages workflows, distributes responsibilities, and adapts strategies to optimize efficiency and reliability across the multi-agent environment.""",
    category=AgentActionCategory.SUPERVISOR,
    deps_schema=extract_deps_schema_from_model(SupervisorAgentDeps),
    output_schema=extract_output_schema_from_model(SupervisorOutput),
    prompt=None,
)


supervisor_bundle = ActionPrototypeBundle(
    name=NODE_NAME,
    prototype=prototype,
    deps_model=SupervisorAgentDeps,
    output_model=SupervisorOutput,
    logic_cls=Supervisor,
)

supervisor_bundle.register()
