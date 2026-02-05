# Gmail Multi Actions test configuration
# Note: You may need to add actual credentials to test_suite/credential.py
from test_suite.credential import AUDITOR_GOOGLE_CREDENTIALS, GOOGLE_CREDENTIALS

TEST_SETTINGS = {
    "test1": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a sequence of Gmail actions: first listen for emails matching a specific goal, then send a response email based on the findings.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "gmail multi actions",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "GmailListener",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "google_token": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "---google-token---",
                            "description": "The Google token to access Gmail API",
                        },
                    },
                    "goal": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related to evidence updates",
                            "description": "Natural language description of what to look for in emails",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SendGmail",
                "order": 1,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "google_token": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "---google-token---",
                            "description": "The Google token to access Gmail API",
                        },
                    },
                    "goal": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send an email to shawn@alltrue.ai with the findings from the email analysis",
                            "description": "Natural language description of what email should be sent",
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
                "google_token": GOOGLE_CREDENTIALS,
                "goal": "Check Inbox, is there any email from Shawn Hong that is related with evidence update.",
            },
            {
                "google_token": GOOGLE_CREDENTIALS,
                "goal": "Send an email to shawn@alltrue.ai, tell him I got the message and found the evidence update email he mentioned.",
            },
        ],
    },
    "test2-check email content from mcp": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a sequence of Gmail actions: first listen for emails matching a specific goal, then send a response email based on the findings.
        """,
        # Agent control configuration
        "agent_control": {
            "name": "gmail multi actions",
            "edges": [],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "GmailListener",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "google_token": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "---google-token---",
                            "description": "The Google token to access Gmail API",
                        },
                    },
                    "goal": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related to evidence updates",
                            "description": "Natural language description of what to look for in emails",
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
                "google_token": AUDITOR_GOOGLE_CREDENTIALS,
                "goal": "Check Inbox, return the content of the latest email.",
            },
        ],
    },
}
