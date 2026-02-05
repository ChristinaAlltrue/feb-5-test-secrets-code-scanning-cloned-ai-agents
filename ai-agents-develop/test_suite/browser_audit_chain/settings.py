from test_suite.credential import (
    GHCO_BUSINESS_UNIT_PASSWORD,
    GHCO_BUSINESS_UNIT_USERNAME,
    GHCO_PASSWORD,
    GHCO_USERNAME,
)

# Browser + Audit Analysis Chain test configuration
TEST_SETTINGS = {
    "Part 1-create_user_list_request": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Navigate to I.T. Assessments and create a new user list request.
        """,
        "entity": {
            "target_business_unit": "Cable Division:Cable ONE",
        },
        # Control variables
        "control_variables": {
            "target_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_USERNAME,
            "password": GHCO_PASSWORD,
            "task": """
            Home page: https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx
            "target_business_unit": "Cable Division:Cable ONE"

            Steps to reach I.T. Assessments page:
            (1) Navigate to 'Filter' input field on the left.
            (2) Input text 'I.T. Assessments (2022 - forward)' to field 'Filter'.
            (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"

            Under the first column Assessment of the table, you can find the clickable cells for different bussiness unit. The names are in <Year> (<Season>) - <Business Unit>
            Find the one for the target business unit and click it.

            After going into the sepcific page, there is a button Add New, click it to create a new request.
            Fill the form with the following 6 entries:
            {
                "Test Period": "Interim"
                "Control Area": "AC01"
                "Request Description": "Current Wide Orbit application user list
Please generate a user list for the WO application, including data generated and all user roles. Include evidence of how the list was generated as well."
                "Date Due": "10/14/2025"
                "Requested by": "agent, AI Auditor" (You need to search the name using the UI)
                "BU Contact(s)": "agent, AI BU"
            }
            Click Save button.
            Record the Tracking ID.
            """,
        },
        # Independent variables configuration
        "independent_variables": {
            "target_business_unit": {
                "args_schema": {
                    "type": "str",
                    "example": "Cable Division:Cable ONE",
                    "description": "The business unit to target for creating user list request",
                }
            }
        },
    },
    "Part 1-upload_sampled_user_list": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Navigate to I.T. Assessments and create a new user list request.
        """,
        "entity": {
            "target_business_unit": "Cable Division:Cable ONE",
        },
        # Control variables
        "control_variables": {
            "target_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_USERNAME,
            "password": GHCO_PASSWORD,
            "task": """Starting page: https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3113377%26moduleId%3d3060

After going into the specific page, wait a 5s for the page to load, click into the 4th request and click EDIT.
Upload and attach the interim evidence \'/home/sum/Documents/Github/ai-agents/UserData/00000000-0000-0000-0000-000000000000/11111111-1111-1111-1111-111111111111/8c1fc502-fc3a-4a3b-9abd-6438c04be27b/output.xlsx\' to the request.
There may have other files attached, do not delete them.
Click Save button.

Record the Tracking ID shown on the page.""",
        },
        # Independent variables configuration
        "independent_variables": {
            "target_business_unit": {
                "args_schema": {
                    "type": "str",
                    "example": "Cable Division:Cable ONE",
                    "description": "The business unit to target for creating user list request",
                }
            }
        },
    },
    "Part 2-sampling_test": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a browser-based data collection followed by audit analysis.

        This workflow demonstrates:
        1. Using Audit Analysis Browser Agent to navigate and download audit files
        2. Passing downloaded files to Audit Analysis Agent for processing
        3. Generating comprehensive audit reports from collected evidence
        """,
        # Agent control configuration
        "agent_control": {
            "name": "browser_audit_chain",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "AuditAnalysisBrowserAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "target_business_unit": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": "ARCS",
                            "description": "List of business units to target for file download",
                        },
                    },
                    "target_url": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                            "description": "GHCO target URL to navigate from",
                        },
                    },
                    "task": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Navigate to I.T. Assessments and download files for target business units",
                            "description": "Task instructions for the browser agent",
                        },
                    },
                    "username": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "test_user",
                            "description": "Username for authentication",
                        },
                    },
                    "password": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "test_password",
                            "description": "Password",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "AuditAnalysisAgent",
                "order": 1,
                "control_variables": {},
                "reference_variables": {
                    "files_to_upload": {
                        "value_type": "ref",
                        "action_index": 0,
                        "field": "files",
                    },
                    "business_units": {
                        "value_type": "ref",
                        "action_index": 0,
                        "field": "business_units",
                    },
                },
                "independent_variable_schema": {
                    "report_instructions": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": """
                            Generate comprehensive audit report with:
                            1. Executive Summary - key findings overview
                            2. Business Unit Analysis - changes by unit
                            3. Control Testing Results - authorization, accuracy, timing
                            4. Risk Assessment - compliance and security implications
                            5. Recommendations - follow-up actions required

                            Use frequency-based sampling methodology:
                            - >260 occurrences: 20 samples
                            - 53-260: 15 samples
                            - 13-52: 3 samples
                            - 5-12: 1 sample
                            - 2-4: 1 sample
                            - 1: 1 sample
                            """,
                            "description": "Instructions for audit report generation",
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
                "target_business_unit": ["ARCS"],
                "target_url": "https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3114054%26moduleId%3d2441",  # this is not used currently
                "task": "Go to https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3114054%26moduleId%3d2441 and download all the files on this page",
                "username": GHCO_USERNAME,
                "password": GHCO_PASSWORD,
            },
            {
                "report_instructions": """
            Here is the mapping of the frequency and sample size, you have to use it when you generate the report.
                FREQUENCY_MAPPING = {
                "> 260": "Multiple Times Per Day",
                "53-260": "Daily",
                "13-52": "Weekly",
                "5-12": "Monthly",
                "3-4": "Quarterly",
                "2": "Semi-Annual",
                "1": "Annual"
                }

                SAMPLE_SIZE_MAPPING = {
                    "Multiple Times Per Day": 20,
                    "Daily": 15,
                    "Weekly": 3,
                    "Monthly": 1,
                    "Quarterly": 1,
                    "Semi-Annual": 1,
                    "Annual": 1
                }
                """
            },
        ],
    },
    "Part 3-testing_provisioning_test": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Execute a browser-based data collection followed by audit analysis.

        This workflow demonstrates:
        1. Using Audit Analysis Browser Agent to navigate and download audit files
        2. Passing downloaded files to Audit Analysis Agent for processing
        3. Generating comprehensive audit reports from collected evidence
        """,
        # Agent control configuration
        "agent_control": {
            "name": "browser_audit_chain",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "AuditAnalysisBrowserAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "target_business_unit": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": '["ARCS", "GAM"]',
                            "description": "List of business units to target for file download",
                        },
                    },
                    "target_url": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                            "description": "GHCO target URL to navigate from",
                        },
                    },
                    "task": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Navigate to I.T. Assessments and download files for target business units",
                            "description": "Task instructions for the browser agent",
                        },
                    },
                    "username": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "test_user",
                            "description": "Username for authentication",
                        },
                    },
                    "password": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "test_password",
                            "description": "Password",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "AuditAnalysisAgent",
                "order": 1,
                "control_variables": {},
                "reference_variables": {
                    "files_to_upload": {
                        "value_type": "ref",
                        "action_index": 0,
                        "field": "files",
                    },
                    "business_units": {
                        "value_type": "ref",
                        "action_index": 0,
                        "field": "business_units",
                    },
                },
                "independent_variable_schema": {
                    "report_instructions": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": """
                            Generate comprehensive audit report with:
                            1. Executive Summary - key findings overview
                            2. Business Unit Analysis - changes by unit
                            3. Control Testing Results - authorization, accuracy, timing
                            4. Risk Assessment - compliance and security implications
                            5. Recommendations - follow-up actions required

                            Use frequency-based sampling methodology:
                            - >260 occurrences: 20 samples
                            - 53-260: 15 samples
                            - 13-52: 3 samples
                            - 5-12: 1 sample
                            - 2-4: 1 sample
                            - 1: 1 sample
                            """,
                            "description": "Instructions for audit report generation",
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
                "target_business_unit": ["Dekko"],
                "target_url": "https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3114053%26moduleId%3d2441",  # this is not used currently
                "task": "Go to https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3114053%26moduleId%3d2441 and download all the files on this page",
                "username": GHCO_USERNAME,
                "password": GHCO_PASSWORD,
            },
            {
                "report_instructions": """
            Here is the mapping of the frequency and sample size, you have to use it when you generate the report.
                FREQUENCY_MAPPING = {
                "> 260": "Multiple Times Per Day",
                "53-260": "Daily",
                "13-52": "Weekly",
                "5-12": "Monthly",
                "3-4": "Quarterly",
                "2": "Semi-Annual",
                "1": "Annual"
                }

                SAMPLE_SIZE_MAPPING = {
                    "Multiple Times Per Day": 20,
                    "Daily": 15,
                    "Weekly": 3,
                    "Monthly": 1,
                    "Quarterly": 1,
                    "Semi-Annual": 1,
                    "Annual": 1
                }
                """
            },
        ],
    },
    "Additional-Full download reliability": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Navigate to I.T. Assessments and create a new user list request.
        """,
        "entity": {
            "target_business_unit": "Cable Division:Cable ONE",
        },
        # Control variables
        "control_variables": {
            "target_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_BUSINESS_UNIT_USERNAME,
            "password": GHCO_BUSINESS_UNIT_PASSWORD,
            "task": """Starting page: https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3114816%26moduleId%3d2441

After going into the specific page, wait 5s for the page to load.
Download all the files on this page.
Plan before downloading and ensure you have downloaded all the files at the end.
""",
        },
        # Independent variables configuration
        "independent_variables": {
            "target_business_unit": {
                "args_schema": {
                    "type": "str",
                    "example": "Cable Division:Cable ONE",
                    "description": "The business unit to target for creating user list request",
                }
            }
        },
    },
}
