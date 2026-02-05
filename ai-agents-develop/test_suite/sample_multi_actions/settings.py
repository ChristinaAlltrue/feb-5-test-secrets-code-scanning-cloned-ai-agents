# Navigation Control test configuration
TEST_SETTINGS = {
    "test1": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a sequence of navigation actions to demonstrate control flow and variable passing between actions.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "sample control",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "sample",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "input": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "int",
                            "example": "5",
                            "description": "a number",
                        },
                    }
                },
            },
            {
                "action_prototype_name": "sample",
                "order": 1,
                "control_variables": {},
                "reference_variables": {
                    "input": {"value_type": "ref", "action_index": 0, "field": "output"}
                },
                "independent_variable_schema": {},
            },
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [{"input": 5}, {}],
    }
}
