# Generic Gmail Agent test configuration
# Note: You may need to add actual credentials to test_suite/credential.py
from test_suite.credential import GOOGLE_CREDENTIALS

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Run the generic Gmail agent to accomplish the specified goal.
        Provide Google credentials in entity variables under `google_token`.
        """,
        "entity": {
            "credentials": {"google_token": GOOGLE_CREDENTIALS},
            "goal": "Send an email to shawn@alltrue.ai confirming I received his message.",
            "expected_output": "Email subject, recipients, and your workflow",
        },
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables (ArgsDeps) - use schema fields so CLI can infer
        "independent_variables": {
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Search inbox for the latest message from John and summarize it",
                    "description": "Natural language goal for the Gmail agent",
                }
            },
            "credentials": {
                "args_schema": {
                    "type": "dictonary",
                    "example": "---google-token---",
                    "description": "The Google token to access Gmail API",
                }
            },
            "expected_output": {
                "args_schema": {
                    "type": "string",
                    "example": "Email subject, recipients, and send confirmation",
                    "description": "What the output should include",
                }
            },
        },
    },
}
