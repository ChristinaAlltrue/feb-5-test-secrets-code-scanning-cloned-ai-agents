SHORT_BROWSER_CASE = {
    "SHORT-BROWSER-CASE": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK**
        """,
        # Agent control configuration
        "agent_control": {
            "name": "Supervisor Agent for Short Browser Case",
            "edges": [
                {"source": 0, "target": 1, "condition": ""},
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
        ],
        "independent_variables": [
            {
                "credentials": {},
                "task_description": """
                go to https://github.com/pydantic/pydantic/tree/main/docs/
                click on img and download the logfire_span.png
                """,
                "additional_description": "",
                "tools": ["browser_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": """
                navigate to https://github.com/pydantic/pydantic/tree/main/docs/
                click on img and download the rich_pydantic.png
                """,
                "additional_description": """
                """,
                "tools": ["browser_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
        ],
    },
}
