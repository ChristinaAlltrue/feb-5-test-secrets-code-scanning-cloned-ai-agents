# Test settings for File Collection Agent
# Note: You may need to add actual credentials or URLs to test_suite/credential.py
from test_suite.credential import (
    AUDITOR_GOOGLE_CREDENTIALS,
    GHCO_PASSWORD,
    GHCO_USERNAME,
)

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        Create GHCO requests for the specified software applications.
        Login to the GHCO system and submit requests for each software in the list.
        Provide tracking IDs and confirmation of successful request creation.
        """,
        "entity": {
            "homepage_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_USERNAME,
            "password": GHCO_PASSWORD,
            "bu_contact": "agent, AI BU",
            "software_list": "Wide Orbit, GAM",
            "target_business_unit": "Cable Division:Cable ONE",
            "google_token": AUDITOR_GOOGLE_CREDENTIALS,
        },
        # Example of control variables (PrimitiveDeps)
        "action_prototype_name": "FileCollectionAgent",
        "control_variables": {},
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "homepage_url": {
                "args_schema": {
                    "type": "string",
                    "example": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                    "description": "The homepage URL of the GHCO system",
                }
            },
            "username": {
                "args_schema": {
                    "type": "string",
                    "example": "user",
                    "description": "Username for authentication",
                }
            },
            "password": {
                "args_schema": {
                    "type": "string",
                    "example": "••••••••",
                    "description": "Password for authentication",
                }
            },
            "bu_contact": {
                "args_schema": {
                    "type": "string",
                    "example": "agent, AI BU",
                    "description": "Business Unit contact person for the requests",
                }
            },
            "software_list": {
                "args_schema": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": '["Wide Orbit", "GAM", "ARCS"]',
                    "description": "List of software applications to create requests for",
                }
            },
            "target_business_unit": {
                "args_schema": {
                    "type": "string",
                    "example": "Cable Division:Cable ONE",
                    "description": "The target business unit for the requests",
                }
            },
            "google_token": {
                "args_schema": {
                    "type": "string",
                    "example": "{}",
                    "description": "Google credential string",
                }
            },
        },
    },
}
