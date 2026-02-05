from uuid import UUID, uuid4

from alltrue.agents.schema.action_execution import (
    ActionInstance,
    ArgsDeps,
    ArgsDepsSchema,
)
from alltrue.agents.schema.control_execution import Edge, PostControlExecutionRequest

from test_suite.credential import GOOGLE_CREDENTIALS


def get_sample_two_action():
    """Factory function that generates fresh UUIDs each time it's called."""
    return {
        "sample two action": PostControlExecutionRequest(
            control_id=UUID("00000000-0000-0000-0000-000000000000"),
            entity_id=UUID("11111111-1111-1111-1111-111111111111"),
            control_execution_id=uuid4(),
            compliance_instruction="""
            **SKIP COMPLIANCE CHECK** Execute two supervisor agent actions in sequence.

            Action 1: Check if there are any emails related to REQ-3114054.
            Action 2: Send the findings from Action 1 to shaw@alltrue.ai.
            """,
            action_instances=[
                ActionInstance(
                    id=uuid4(),
                    action_prototype_name="SupervisorAgent",
                    order=0,
                    control_variables={},
                    reference_variables={},
                    independent_variables={
                        "credentials": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="object",
                                example="{}",
                                description="Key-value credential map available to tools",
                            ),
                        ),
                        "task_description": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="Check if there are any emails related with REQ-3114054",
                                description="Primary task description for the supervisor agent",
                            ),
                        ),
                        "additional_description": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="if there is an email, summarize subjects, senders  Google token used for email tool is {GOOGLE_CREDENTIALS}",
                                description="Additional context or requirements for the output",
                            ),
                        ),
                        "tools": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="list",
                                example='["generic_gmail_agent_tool"]',
                                description="List of tool ids to include for the agent",
                            ),
                        ),
                        "model_provider": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="gemini",
                                description="The model provider to use for the agent",
                            ),
                        ),
                        "model_name": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="gemini-2.5-flash",
                                description="The model name to use for the agent",
                            ),
                        ),
                    },
                ),
                ActionInstance(
                    id=uuid4(),
                    action_prototype_name="SupervisorAgent",
                    order=1,
                    control_variables={},
                    reference_variables={},
                    independent_variables={
                        "credentials": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="object",
                                example="{}",
                                description="Key-value credential map available to tools",
                            ),
                        ),
                        "task_description": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="Send your findings base on previous result to shawn@alltrue.ai",
                                description="Primary task description for the supervisor agent",
                            ),
                        ),
                        "additional_description": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="show me the content you send  Google token used for email tool is {GOOGLE_CREDENTIALS}",
                                description="Additional context or requirements for the output",
                            ),
                        ),
                        "tools": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="list",
                                example='["generic_gmail_agent_tool"]',
                                description="List of tool ids to include for the agent",
                            ),
                        ),
                        "model_provider": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="openai",
                                description="The model provider to use for the agent",
                            ),
                        ),
                        "model_name": ArgsDeps(
                            value_type="args",
                            args_schema=ArgsDepsSchema(
                                type="string",
                                example="gpt-4.1",
                                description="The model name to use for the agent",
                            ),
                        ),
                    },
                ),
            ],
            edges=[Edge(source=0, target=1, condition="")],
            entity_exec_args=[
                {
                    "credentials": {},
                    "task_description": "Check if there are any emails related with REQ-3114054",
                    "additional_description": f"if there is an email, summarize subjects, senders  Google token used for email tool is {GOOGLE_CREDENTIALS}",
                    "tools": ["generic_gmail_agent_tool"],
                    "model_provider": "gemini",
                    "model_name": "gemini-2.5-flash",
                },
                {
                    "credentials": {},
                    "task_description": "Send your findings base on previous result to shawn@alltrue.ai",
                    "additional_description": f"show me the content you send  Google token used for email tool is {GOOGLE_CREDENTIALS}",
                    "tools": ["generic_gmail_agent_tool"],
                    "model_provider": "openai",
                    "model_name": "gpt-4.1",
                },
            ],
        )
    }


# For backward compatibility, also expose as a dict (but it will be regenerated on each access)
SAMPLE_TWO_ACTION = get_sample_two_action()
