from test_suite.credential import (
    AUDITOR_GOOGLE_CREDENTIALS,
    GHCO_PASSWORD,
    GHCO_USERNAME,
)

# Browser + Audit Analysis Chain test configuration
TEST_SETTINGS = {
    "End to End Test": {
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
            "name": "End to end testing",
            "edges": [{"source": 0, "target": 1, "condition": ""}],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "AuditorManager",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "homepage_url": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                            "description": "The homepage URL of the GHCO system",
                        },
                    },
                    "username": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "user",
                            "description": "Username for authentication",
                        },
                    },
                    "password": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "••••••••",
                            "description": "Password for authentication",
                        },
                    },
                    "bu_contact": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "agent, AI BU",
                            "description": "Business Unit contact person for the requests",
                        },
                    },
                    "software_list": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": '["Wide Orbit", "GAM", "ARCS"]',
                            "description": "List of software applications to create requests for",
                        },
                    },
                    "target_business_unit": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Cable Division:Cable ONE",
                            "description": "The target business unit for the requests",
                        },
                    },
                    "google_token": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "{}",
                            "description": "Google credential string",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Create GHCO requests for the specified software applications.",
                            "description": "Description of the overall task for file collection",
                        },
                    },
                    "user_list_instructions": {
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
            {
                "action_prototype_name": "ProvisioningAuditorManager",
                "order": 1,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "homepage_url": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                            "description": "The homepage URL of the GHCO system",
                        },
                    },
                    "username": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "user",
                            "description": "Username for authentication",
                        },
                    },
                    "password": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "••••••••",
                            "description": "Password for authentication",
                        },
                    },
                    "bu_contact": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "agent, AI BU",
                            "description": "Business Unit contact person for the requests",
                        },
                    },
                    "software_list": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": '["Wide Orbit", "GAM", "ARCS"]',
                            "description": "List of software applications to create requests for",
                        },
                    },
                    "target_business_unit": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Cable Division:Cable ONE",
                            "description": "The target business unit for the requests",
                        },
                    },
                    "google_token": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "{}",
                            "description": "Google credential string",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Create GHCO requests for the specified software applications.",
                            "description": "Description of the overall task for file collection",
                        },
                    },
                    "provisioning_instructions": {
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
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [
            {
                "homepage_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                "username": GHCO_USERNAME,
                "password": GHCO_PASSWORD,
                "bu_contact": "agent, AI BU",
                "software_list": "Wide Orbit, GAM",
                "target_business_unit": "2025 Q4 Cable Division:Cable ONE",
                "google_token": AUDITOR_GOOGLE_CREDENTIALS,
                "task_description": """Your tasks:
1. Create requests for each software application using the browser_agent and extract tracking ID(s), ensure all requests are created successfully, retry once when browser_agent returns error
2. Wait for Business Unit (BU) to submit required files by using trigger_pause
3. When resuming, check the inbox and get the email content of the tracking ID(s), download the file from the request page using the link provided in the email and wait again for any remaining software applications, pause again if needed. Never proceed until there is at least one file downloaded for each software application
4. Prepare files to compare from Google Drive. Pause when you cannot find the file to compare for any software application, wait for human to upload the missing file to Google Drive and resume
5. Return all the paths of files

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

When resuming from BU submission:
- The email subject would be in the format of Updated Request for ..., get the link to the request page from the body, and use browser_agent to download the file from the request page
    - example task: "Go to <link>. Click to download all the files shown on this page. Close the browser after downloading or when there is no file to download. Return the path of the downloaded file."

When preparing files to compare:
- The files are organized in the folder 1UqUcpHpVI-85-83Vhz_Ln_BcmGGBZ2qp
- The files are put into different folders according to their software names
- Give the current file name as an example and ask the tool `find_and_download_previous_file` to return the latest file to compare

Always be thorough and provide detailed feedback about the request creation and file collection process.""",
                "user_list_instructions": """REPORT REQUIREMENTS:
- Compare current vs previous versions
- Identify new accounts, permission changes, updates
- Ignore removed accounts when performing analysis
- Calculate populations and sample sizes using frequency mapping (>260=20, 53-260=15, etc.)
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

**Sampling Rules (to align with auditor practice):**
- When multiple applications are included, weight sample selection by each application’s population size of new/updated users.
- Determine frequency by extrapolating observed interim counts to a full year when necessary.
- Target sample size and cap
  - Use the frequency mapping to set the target sample size (e.g., Daily = 15). Enforce a hard cap at the mapped size.
- Priority rules within the cap
  - Select within the cap using this order:
    1) Updated users whose access level increased to elevated (admin/privileged)
    2) New elevated users (admin/privileged)
    3) Other updated users (role/group changes not elevated)
    4) New standard users
  - If a priority tier has more candidates than remaining slots, pick by risk (external/service accounts, highest privilege, cross-system elevated), then randomize the remainder. Do not exceed the cap.
- Application weighting
  - Weight the 15 within the cap by each application’s population share (quota = round(cap × app_population / total_population)). Allow a small flex (±1) to honor the priority rules. Keep total at the cap.
- Interim vs. year-end increments
  - Interim default = mapped size only (e.g., 15). Year-end incremental = +5 only if explicitly requested and no exceptions found. Do not add year-end items to the interim file by default.
- Documentation
  - Document counts by priority tier, risk factors used, any weighting adjustments, and final selection rationale.""",
            },
            {
                "homepage_url": "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx",
                "username": GHCO_USERNAME,
                "password": GHCO_PASSWORD,
                "bu_contact": "agent, AI BU",
                "software_list": "Wide Orbit, GAM",
                "target_business_unit": "2025 Q4 Cable Division:Cable ONE",
                "google_token": AUDITOR_GOOGLE_CREDENTIALS,
                "task_description": """Your tasks:
1. Create a request to the BU asking for evidences, you should upload the User List excel from the previous step.
2. Wait for Business Unit (BU) to submit required files by using trigger_pause
3. Download all the evidence file from the request page

When creating requests:
- Use the provided template and fill in the values
- Extract and record tracking IDs for the request
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
            "Control Area": "AC02"
            "Request Description": "New and updated User Sample
Please provide evidence showing the request, approval and provisioning for the attached list of users."
            "Date Due": <1 week from today (date are usually in MM/DD/YYYY format)>
            "Requested by": "agent, AI Auditor" (You need to search the name using the UI)
            "BU Contact(s)": "{config.bu_contact}"
        }}
        Click Save button.
        Record the Tracking ID.
    </template>

When resuming:
- Check the inbox of the email for notifications about file submissions, the subject would be in the format of Updated Request for ..., get the link to the request page from the email, and use browser_agent to download the file from the request page
    - example task: "Go to <link>. Click to download all the files shown on this page. Close the browser after downloading or when there is no file to download."


Always be thorough and provide detailed feedback about the request creation and file collection process.""",
                "provisioning_instructions": "",
            },
        ],
    },
}
