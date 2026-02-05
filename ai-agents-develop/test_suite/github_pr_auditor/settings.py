from test_suite.credential import GITHUB_TOKEN

# New format with customizable variable types
TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        Determine if the PR is passed the check based on the audit goal.
        """,
        "entity": {
            "target_PR": "https://github.com/AllTrue-ai/ai-agents/pull/89",
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {
            "github_token": GITHUB_TOKEN,
            "goal": """
            1. Check if there is a priority label of high, medium, or low assigned to the PR.,
            2. The time that the PR get approved must be before the time that the PR get merged.
            3. There must be a issue link be mentioned in the comments.
            """,
        },
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "target_PR": {
                "args_schema": {
                    "type": "string",
                    "example": "https://github.com/org/repo/pull/123",
                    "description": "URL of the target pull request to audit",
                }
            }
        },
    },
    "test2-skip-compliance-check": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Determine if the PR is passed the check based on the audit goal.
        """,
        "entity": {
            "target_PR": "https://github.com/AllTrue-ai/ai-agents/pull/89",
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {
            "github_token": GITHUB_TOKEN,
            "goal": """
            1. Check if there is a priority label of high, medium, or low assigned to the PR.,
            2. The time that the PR get approved must be before the time that the PR get merged.
            3. There must be a issue link be mentioned in the comments.
            """,
        },
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "target_PR": {
                "args_schema": {
                    "type": "string",
                    "example": "https://github.com/org/repo/pull/123",
                    "description": "URL of the target pull request to audit",
                }
            }
        },
    },
}
