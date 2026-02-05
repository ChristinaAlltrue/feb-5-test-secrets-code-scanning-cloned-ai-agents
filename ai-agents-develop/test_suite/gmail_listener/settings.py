# Test settings for Gmail Listener agent
# Note: You may need to add actual credentials to test_suite/credential.py
from test_suite.credential import GOOGLE_CREDENTIALS

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Analyze Gmail messages to determine if they match the specified goal.
        Search for relevant emails and provide a clear decision with detailed feedback.
        """,
        "entity": {
            "google_token": GOOGLE_CREDENTIALS,
            "goal": """
            Check Inbox, is there any email from Shawn Hong that is related with evidence update.
            """,
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {},
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "google_token": {
                "args_schema": {
                    "type": "string",
                    "example": "---google-token---",
                    "description": "The Google token to access Gmail API",
                }
            },
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Check if there are any emails related to evidence updates",
                    "description": "Natural language description of what to look for in emails",
                }
            },
        },
    },
    "test2-urgent-emails": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Analyze Gmail messages to determine if there are any urgent emails requiring immediate attention.
        """,
        "entity": {
            "google_token": GOOGLE_CREDENTIALS,
            "goal": """
            Check if there are any urgent emails in the inbox that require immediate attention.
            Look for emails with 'urgent', 'asap', 'immediate', 'critical', 'emergency' in subject or content.
            Also check for emails from important contacts or high-priority senders.
            """,
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {},
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "google_token": {
                "args_schema": {
                    "type": "string",
                    "example": "---google-token---",
                    "description": "The Google token to access Gmail API",
                }
            },
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Check if there are any urgent emails requiring immediate attention",
                    "description": "Natural language description of what to look for in emails",
                }
            },
        },
    },
}
