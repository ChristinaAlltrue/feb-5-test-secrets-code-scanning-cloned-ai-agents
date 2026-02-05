# Test settings for GHCO_connected_agents
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
            "task_description": """
Your tasks:
1. Create requests for each software application using the browser_agent and extract tracking IDs, ensure all requests are created successfully, retry once when browser_agent returns error
2. Wait for Business Unit (BU) to submit required files by using trigger_pause
3. When resuming, indicating some files have been uploaded to a request page, download the file from the request page and wait again for any remaining software applications, pause again if needed
4. Prepare files to compare from Google Drive
5. Return the paths of successfully downloaded files

When creating requests:
- Use the provided template and fill in the software name dynamically
- Extract and record tracking IDs for each request
- Create requests for all software in the list
  Template for giving browser_agent a task:
    <template>
    Target Business Unit: "{config.target_business_unit}"
    Home page: {config.homepage_url}

    Navigate to the home page and wait for 8 seconds for the page to load.

    Steps to reach I.T. Assessments page:
    (1) Navigate to 'Filter' input field on the left.
    (2) Input text 'I.T. Assessments (2022 - forward)' to field 'Filter'.
    (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"

    Under the first column Assessment of the table, you can find the clickable cells for different business unit. The names are in <Year> (<Season>) - <Business Unit>
    Find the one for the target business unit and click it.

    After going into the specific page, there is a button Add New, click it to create a new request.
    Fill the form with the following 6 entries:
    {{
        "Test Period": "Interim"
        "Control Area": "AC01"
        "Request Description": "Current {software} application user list
Please generate a user list for the {software} application, including data generated and all user roles. Include evidence of how the list was generated as well."
        "Date Due": <Two weeks from today (date are usually in MM/DD/YYYY format)>
        "Requested by": "agent, AI Auditor" (You need to search the name using the UI)
        "BU Contact(s)": "{config.bu_contact}"
    }}
    Double check that you filled in all the fields correctly and click the Save button.
    When a warning pop-up shows up, check what's the problem and resolve it accordingly.
    Upon successful save, record and return the Tracking ID shown on the page.
    </template>

When resuming:
- Use check_request_update to get the Tracking ID that received file update
- Check the inbox of the email for notifications about file submissions, the subject would be in the format of Updated Request for ..., get the link to the request page from the email, and use browser_agent to download the file from the request page
    - example task: "Go to <link>. Click to download all the files shown on this page. Close the browser."


When preparing files to compare:
- The files are organized in the folder 1UqUcpHpVI-85-83Vhz_Ln_BcmGGBZ2qp
- The files are put into different folders according to their software names
- Give the current file name as an example and ask the tool `find_and_download_previous_file` to return the latest file to compare

Always be thorough and provide detailed feedback about the request creation and file collection process.""",
            "report_instructions": """
            Here is the mapping of the frequency and sample size, you have to use it when you generate a excel of Detailed Testing Table.
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
        # Example of control variables (PrimitiveDeps)
        "action_prototype_name": "AuditorManager",
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
            "task_description": {
                "args_schema": {
                    "type": "string",
                    "example": "Create GHCO requests for the specified software applications.",
                    "description": "Description of the overall task for file collection",
                }
            },
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
                    - 1-12: 1 sample
                    """,
                    "description": "Instructions for audit report generation",
                },
            },
        },
    },
}
