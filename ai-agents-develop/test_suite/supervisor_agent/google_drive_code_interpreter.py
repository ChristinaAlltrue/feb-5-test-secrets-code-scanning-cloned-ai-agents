from test_suite.credential import GOOGLE_CREDENTIALS

GOOGLE_DRIVE_CODE_INTERPRETER = {
    "GOOGLE-DRIVE-CODE-INTERPRETER": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        Check the generated content.
        if the story file has more than 100 words, it is compliant.
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
                "task_description": "Search my drive for a file called `Agent-test-text` and download it as txt.",
                "additional_description": f"Google token is `google-token`",
                "tools": [{"tool_id": "google_drive_mcp_tool"}],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
            {
                "task_description": "Analyze the story file from previous result and generate a new story with different ending. The new story should be a txt file as well.",
                "additional_description": "",
                "tools": [{"tool_id": "advanced_data_analysis_tool"}],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
        ],
        "credentials": [
            {
                "google-token": {
                    "credential_type": "Secret String",
                    "secret": GOOGLE_CREDENTIALS,
                }
            },
            {
                "google-token": {
                    "credential_type": "Secret String",
                    "secret": GOOGLE_CREDENTIALS,
                }
            },
        ],
    },
}
