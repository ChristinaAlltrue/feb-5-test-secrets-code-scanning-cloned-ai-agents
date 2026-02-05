from test_suite.credential import GHCO_PASSWORD, GHCO_USERNAME

# New format with customizable variable types
TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** The goal is to make sure the all the business units have the files downloaded.
        """,
        "entity": {
            "target_business_unit": "Wide Orbit, GAM, ARCS",
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {
            "login_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_USERNAME,
            "password": GHCO_PASSWORD,
            "navigation_instruction": """
            (1) Navigate to 'Filter' input field on the left.
            (2) input text `I.T. Assessments (2022 - forward)` to field `Filter`.
            (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"
            (4) Click "2025 (ALL) - Cable Division:Cable ONE"
            (5) Download all the files related to the target business units.
            """,
            "report_instruction": """
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
            """,
        },
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "target_business_unit": {
                "args_schema": {
                    "type": "str",
                    "example": "Wide Orbit, GAM, ARCS",
                    "description": "The business unit that the user wants the agent to check",
                }
            }
        },
    },
    "test2": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** The goal is to make sure the all the business units have the files downloaded.
        """,
        "entity": {
            "target_business_unit": "GAM",
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {
            "login_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
            "username": GHCO_USERNAME,
            "password": GHCO_PASSWORD,
            "navigation_instruction": """
            (1) Navigate to 'Filter' input field on the left.
            (2) input text `I.T. Assessments (2022 - forward)` to field `Filter`.
            (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"
            (4) Click "2025 (ALL) - Cable Division:Cable ONE"
            (5) Scroll to the `Test User List 3 - GAM`
            (6) Download these two files: Google-Ad_ManagerUsers-071124_(3).csv,  Google-Ad_Manager_Users-110624_(11).csv
            """,
            "report_instruction": """
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
            """,
        },
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "target_business_unit": {
                "args_schema": {
                    "type": "str",
                    "example": "Wide Orbit, GAM, ARCS",
                    "description": "The business unit that the user wants the agent to check",
                }
            }
        },
    },
}
