# Sample Generic Action test configuration
TEST_SETTINGS = {
    "test1": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a sequence of generic actions to demonstrate parameter interpretation and tool execution flow.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "sample generic control",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "sample_generic_action",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "goal": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Increment the input number 5 by 3",
                            "description": "A natural language goal describing what to do with numbers",
                        },
                    }
                },
            },
            {
                "action_prototype_name": "sample_generic_action",
                "order": 1,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "goal": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Add 10 to the number 7",
                            "description": "A natural language goal describing what to do with numbers",
                        },
                    }
                },
            },
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [
            {"goal": "Increment the input number 5 by 3"},
            {"goal": "Base on the previous result, add by 10"},
        ],
    }
}
