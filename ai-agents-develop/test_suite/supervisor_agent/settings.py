# Supervisor Agent test configuration
# Note: You may need to add actual credentials to test_suite/credential.py
from test_suite.credential import GOOGLE_CREDENTIALS
from test_suite.supervisor_agent.ghco_co2 import GHCO_CO2_CONTROL
from test_suite.supervisor_agent.ghco_dekko_co2 import (
    GHCO_DEKKO_CO2_CONTROL_MULTIPLE,
    GHCO_DEKKO_CO2_CONTROL_SINGLE,
)
from test_suite.supervisor_agent.github_mcp import GITHUB_MCP_TOOL_TEST
from test_suite.supervisor_agent.google_drive_code_interpreter import (
    GOOGLE_DRIVE_CODE_INTERPRETER,
)
from test_suite.supervisor_agent.short_browser_case import SHORT_BROWSER_CASE

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Run the supervisor agent to accomplish the specified task_description
        using the single tool `generic_gmail_agent_tool`. Provide Google credentials in
        entity variables under `credentials.google_token`.
        """,
        "credentials": {
            "google-token": {
                "credential_type": "Secret String",
                "secret": GOOGLE_CREDENTIALS,
            }
        },
        "entity": {
            "task_description": "Send an email to shawn@alltrue.ai confirming I received his message.",
            "additional_description": f"Email subject, recipients, and your workflow Google token used for email tool is `google-token`",
            # Tools available to the supervisor (must match TOOLS_REGISTRY keys)
            "tools": [
                {
                    "tool_id": "generic_gmail_agent_tool",
                }
            ],
            "model_provider": "gemini",
            "model_name": "gemini-2.5-flash",
        },
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables (ArgsDeps) inferred from schema
        "independent_variables": {
            "task_description": {
                "args_schema": {
                    "type": "string",
                    "example": "Search inbox for the latest message from John and summarize it",
                    "description": "Primary task description for the supervisor agent",
                }
            },
            "additional_description": {
                "args_schema": {
                    "type": "string",
                    "example": "Email subject, recipients, and send confirmation",
                    "description": "Additional context or output requirements",
                }
            },
            "tools": {
                "args_schema": {
                    "type": "array",
                    "example": """["generic_gmail_agent_tool"]""",
                    "description": "List of tool ids allowed for the supervisor agent",
                }
            },
            "model_provider": {
                "args_schema": {
                    "type": "string",
                    "example": "openai",
                    "description": "The model provider to use for the supervisor agent",
                }
            },
            "model_name": {
                "args_schema": {
                    "type": "string",
                    "example": "gpt-4.1",
                    "description": "The model name to use for the supervisor agent",
                }
            },
        },
    },
    "two_actions": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute two supervisor agent actions in sequence.

        Action 1: Check if there are any emails related to REQ-3114054.
        Action 2: Send the findings from Action 1 to shaw@alltrue.ai.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "supervisor two actions",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Primary task description for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Summarize subjects, senders, and snippets of related emails",
                            "description": "Additional context or output requirements",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 1,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Summarize subjects, senders, and snippets of related emails",
                            "description": "Additional context or output requirements",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Primary task description for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [
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
    },
    "Pause-Resume": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute two supervisor agent actions in sequence.
        Action 1: Check if there are any emails related to REQ-3114054.
        Action 2: Send the findings from Action 1 to shaw@alltrue.ai.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "supervisor pause-resume four actions",
            "edges": [
                {"source": 0, "target": 1, "condition": ""},
                {"source": 1, "target": 2, "condition": ""},
                {"source": 2, "target": 3, "condition": ""},
            ],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 1,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 2,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 3,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [
            {
                "credentials": {},
                "task_description": "The beginning number is 3 count up to 4. Go to next step. The expected output is the current number.",
                "additional_description": f"Google token used for email tool is {GOOGLE_CREDENTIALS}",
                "tools": [],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": "On resume, do not send email again, consider the task complete, otherwise, send an email to segalinc@alltrue.ai describing what the agent did in the last step, then request a pause. Expected output: the current number.",
                "additional_description": f"Google token used for email tool is {GOOGLE_CREDENTIALS}",
                "tools": ["generic_gmail_agent_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": "Based on previous result, count the number up by 1, do not pause. Output the current number.",
                "additional_description": "",
                "tools": [],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
            {
                "credentials": {},
                "task_description": "Send an email to segalinc@alltrue.ai summarizing which number you started from, what you did to the number, and what steps you took to reach here, do not pause",
                "additional_description": f"Google token used for email tool is {GOOGLE_CREDENTIALS}",
                "tools": ["generic_gmail_agent_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
        ],
    },
    **GHCO_CO2_CONTROL,
    **SHORT_BROWSER_CASE,
    **GHCO_DEKKO_CO2_CONTROL_SINGLE,
    **GHCO_DEKKO_CO2_CONTROL_MULTIPLE,
    **GITHUB_MCP_TOOL_TEST,
    **GOOGLE_DRIVE_CODE_INTERPRETER,
}
