from uuid import UUID, uuid4

from alltrue.agents.schema.action_execution import (
    ActionInstance,
    ArgsDeps,
    ArgsDepsSchema,
    RefDeps,
)
from alltrue.agents.schema.control_execution import Edge, PostControlExecutionRequest


def get_test_settings():
    """Factory function that generates fresh UUIDs each time it's called."""
    return {
        "test1": PostControlExecutionRequest(
            control_id=UUID("00000000-0000-0000-0000-000000000000"),
            entity_id=UUID("11111111-1111-1111-1111-111111111111"),
            control_execution_id=uuid4(),
            compliance_instruction=(
                "**SKIP COMPLIANCE CHECK** Execute a sequence of navigation actions to demonstrate "
                "control flow and variable passing between actions."
            ),
            action_instances=[
                ActionInstance(
                    id=uuid4(),
                    action_prototype_name="sample",
                    order=0,
                    control_variables={},
                    reference_variables={},
                    independent_variables={
                        "input": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="int", example="5", description="a number"
                            ),
                        )
                    },
                    subagents=[],
                ),
                ActionInstance(
                    id=uuid4(),
                    action_prototype_name="sample",
                    order=1,
                    control_variables={},
                    reference_variables={
                        "input": RefDeps(
                            value_type="ref", action_index=0, field="output"
                        )
                    },
                    independent_variables={},
                    subagents=[],
                ),
            ],
            edges=[Edge(source=0, target=1, condition="")],
            entity_exec_args=[{"input": 5}, {}],
        )
    }


# For backward compatibility, also expose as a dict (but it will be regenerated on each access)
TEST_SETTINGS = get_test_settings()
