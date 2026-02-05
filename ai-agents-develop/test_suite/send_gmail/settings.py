# Test settings for Send Gmail agent
# Note: You may need to add actual credentials to test_suite/credential.py
from test_suite.credential import GOOGLE_CREDENTIALS

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Send an email based on the specified goal.
        Parse the goal to extract recipient, subject, and body, then send the email.
        """,
        "entity": {
            "google_token": GOOGLE_CREDENTIALS,
            "goal": """
            Send an email to shawn@alltrue.ai, tell him I got the message
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
                    "example": "Send an email to john@example.com with subject 'Meeting Reminder' and body 'Don't forget about our meeting tomorrow at 2 PM'",
                    "description": "Natural language description of what email should be sent, including recipient, subject, and content",
                }
            },
        },
    },
}
