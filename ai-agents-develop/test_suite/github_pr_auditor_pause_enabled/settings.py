from test_suite.credential import (
    GITHUB_PASSWORD,
    GITHUB_TOKEN,
    GITHUB_USERNAME,
    MFA_SECRET,
)

# New format with customizable variable types
TEST_SETTINGS = {
    "Pause": {
        "control_instruction": """
        Determine if the PR is passed the check based on the audit goal.
        """,
        "entity": {
            "goal": """
            1. Check if there is a priority label of high, medium, or low assigned to the PR.,
            2. The time that the PR get approved must be before the time that the PR get merged.
            3. There must be a issue link be mentioned in the comments.
            """,
            "target_PR": "https://github.com/AllTrue-ai/ai-agents/pull/110",
        },
        "control_variables": {
            "github_token": GITHUB_TOKEN,
            "username": GITHUB_USERNAME,
            "password": GITHUB_PASSWORD,
            "mfa_secret": "",
            "pause_enabled": True,
        },
        "independent_variables": {
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Check if there is a priority label of high, medium, or low assigned to the PR.,",
                    "description": "The goal of the audit",
                }
            },
            "target_PR": {
                "args_schema": {
                    "type": "string",
                    "example": "https://github.com/AllTrue-ai/ai-agents/pull/110",
                    "description": "URL of the target pull request to audit",
                }
            },
        },
    },
    "Resume": {
        "control_instruction": """
        Determine if the PR is passed the check based on the audit goal.
        """,
        "entity": {
            "goal": """
            1. Check if there is a priority label of high, medium, or low assigned to the PR.,
            2. The time that the PR get approved must be before the time that the PR get merged.
            3. There must be a issue link be mentioned in the comments.
            """,
            "target_PR": "https://github.com/AllTrue-ai/ai-agents/pull/110",
        },
        "control_variables": {
            "github_token": GITHUB_TOKEN,
            "username": GITHUB_USERNAME,
            "password": GITHUB_PASSWORD,
            "mfa_secret": MFA_SECRET,
            "pause_enabled": True,
        },
        "independent_variables": {
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Check if there is a priority label of high, medium, or low assigned to the PR.,",
                    "description": "The goal of the audit",
                }
            },
            "target_PR": {
                "args_schema": {
                    "type": "string",
                    "example": "https://github.com/AllTrue-ai/ai-agents/pull/110",
                    "description": "URL of the target pull request to audit",
                }
            },
        },
    },
}
