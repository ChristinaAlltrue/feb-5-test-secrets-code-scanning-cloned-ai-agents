from test_suite.credential import GOOGLE_CREDENTIALS

GHCO_DEKKO_CO2_CONTROL_SINGLE = {
    "GHCO-DEKKO-CO2-CONTROL": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK**
        """,
        # Agent control configuration
        "agent_control": {
            "name": "Supervisor Agent for GHCO DEKKO CO2 Control",
            "edges": [],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "credentials": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "object",
                            "example": """{"google_token": "---google-token---"}""",
                            "description": "Key-value credential map available to tools",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            }
        ],
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables for entity execution
        "independent_variables": [
            {
                "credentials": {},
                "task_description": """

# Manual for IT Change Control Audit Testing

## 1.0 Objective

The purpose of this procedure is to provide a standardized set of instructions for testing the effectiveness of IT change management controls. This process ensures that all changes to in-scope systems are properly requested, tested, approved, and implemented, thereby maintaining the integrity of the IT environment.

## 2.0 Procedure Overview

The audit process consists of three primary phases:

1.  **Population Gathering & Sampling:** Obtaining a complete and accurate list of all changes within the audit period and selecting a sample for testing.
2.  **Detailed Evidence Testing:** Examining the documentation for each sampled change to verify that key control steps were followed.
3.  **Analysis & Conclusion:** Documenting the results and identifying any exceptions or control weaknesses.

---

## 3.0 Phase 1: Population Gathering & Sampling

### 3.1 Define Scope and Request Population

1.  **Initiate Request:** Formally request a complete listing of all changes for the target application (e.g., BPIX) and a specific audit period (e.g., January 1st to August 1st).
2.  **Request Supporting Evidence:** In the request, specify that two forms of evidence are required from the system owner:
    * A screenshot of the system query or filters used to generate the list. This validates the completeness of the population.
    * The complete change ticket documentation (e.g., PDF files) for every change on the generated list.

### 3.2 Validate Population and Select Sample

1.  **Verify Filters:** Upon receipt, review the screenshot of the filters. Ensure the criteria correctly match the audit scope.
    * **Guidance & Example:** The filters should clearly define the population. For instance, the query should show filters for:
        * `Status: Completed`
        * `Scope: In Scope (SOX)`
        * `Year: [Current Audit Year]`

2.  **Determine Sample Size:** Count the total number of changes in the validated population. Based on your organization's audit methodology and the population size, determine the appropriate sample size for testing.
    * **Guidance & Example:** For a small population (e.g., 4 changes), a sample of 2 might be sufficient for interim testing, with a plan to test additional changes later in the year.

---

## 4.0 Phase 2: Detailed Evidence Testing

For each change ticket selected in your sample, perform the following steps to extract evidence from the source document (PDF) and record it in the destination document (Excel Testing Table).

### 4.1 Data Extraction and Recording

Use the following table as a guide to map information from the change ticket PDF to your Excel testing worksheet.

[
{
"excel_field": "Change Ticket #",
"how_to_find_in_pdf": "Locate the unique Project or Request Number. This is typically in the document header. Example: 'SPRC2-XXXXXX'.",
"purpose_rationale": "Serves as the unique identifier for the change being tested."
},
{
"excel_field": "Change Type",
"how_to_find_in_pdf": "Find the 'Type' field, usually under a 'Project Information' section. Example: 'Project Request'.",
"purpose_rationale": "Categorizes the nature of the change."
},
{
"excel_field": "System Impacted",
"how_to_find_in_pdf": "May need to be inferred from the 'Name of Project' field or technical object descriptions within the ticket. Example: 'BPIX'.",
"purpose_rationale": "Identifies the specific application or system being modified."
},
{
"excel_field": "Description of change",
"how_to_find_in_pdf": "Copy the text from the 'Name of Project' or a similar summary field.",
"purpose_rationale": "Provides a clear, concise summary of the change's purpose."
},
{
"excel_field": "Developer",
"how_to_find_in_pdf": "Identify the name listed in the 'Suggested Developer' or 'IT Resources' field.",
"purpose_rationale": "Records who was responsible for the technical development of the change."
},
{
"excel_field": "Evidence of testing?",
"how_to_find_in_pdf": "Look for a section titled 'Analyst Evaluation' or similar. If the developer has documented their testing steps and results, record 'Yes.'",
"purpose_rationale": "Confirms that testing was performed. Developer-level unit testing is the minimum requirement."
},
{
"excel_field": "Change Tester",
"how_to_find_in_pdf": "Identify the author of the 'Analyst Evaluation' section. Cross-reference with the 'Testing Validation' section.",
"purpose_rationale": "Documents who performed the testing. Check for fields like 'Does anyone else need to test these changes?' to see if testing was limited to the developer."
},
{
"excel_field": "Testing Date",
"how_to_find_in_pdf": "In the 'Phase Tracking' table at the end of the document, find the 'Completed' date for the 'Analyst Evaluation' activity.",
"purpose_rationale": "Establishes the date when testing was successfully completed."
},
{
"excel_field": "Pre-production approver",
"how_to_find_in_pdf": "In the 'Phase Tracking' table, find the name associated with the 'IT Review' or equivalent pre-approval activity.",
"purpose_rationale": "Identifies the manager or lead who formally approved the change to proceed."
},
{
"excel_field": "Approval date",
"how_to_find_in_pdf": "In the 'Phase Tracking' table, find the 'Completed' date for the 'IT Review' activity.",
"purpose_rationale": "Records the date of the formal, pre-implementation approval."
},
{
"excel_field": "Migration to Production by",
"how_to_find_in_pdf": "In the 'Phase Tracking' table, find the name associated with the 'Project Installation' or deployment activity.",
"purpose_rationale": "Identifies the individual who moved the code into the live production environment."
},
{
"excel_field": "Migration date",
"how_to_find_in_pdf": "In the 'Phase Tracking' table, find the 'Completed' date for the 'Project Installation' activity.",
"purpose_rationale": "Marks the specific date the change went live and became active for users."
}
]

---

## 5.0 Phase 3: Analysis & Conclusion

After recording the data for all samples, analyze the findings to form a conclusion.

### 5.1 Identify and Document Exceptions

Review the completed testing table for potential control issues or deviations from standard procedure.

1.  **Check for Segregation of Duties (SoD) Conflicts:**
    * **Situation:** Compare the `Developer`, `Change Tester`, and `Migration to Production by` fields. If the same person performed development and migration to production, an SoD conflict exists.
    * **Correspondence/Action:** Document this in the "Exceptions" column. If this is a known risk in a small IT shop, reference any mitigating controls that are tested elsewhere. *Example Note: "Developer also migrated change to production. This is a known issue mitigated by post-implementation reviews."*

2.  **Verify Process Adherence:**
    * **Situation:** Compare the key dates (`Approval date`, `Testing Date`, `Migration date`). Does the sequence make sense? For example, approval should ideally occur before migration.
    * **Correspondence/Action:** Document the observed process. *Example Note: "The process shows that formal approval is performed prior to development and testing, which is the established workflow for this business unit."*

3.  **Confirm Testing Requirements:**
    * **Situation:** Was testing performed by someone other than the developer?
    * **Correspondence/Action:** If not, confirm that the change ticket did not require it. *Example Note: "Per the 'Testing Validation' section of the ticket, no testing was required beyond the developer's unit test."*

### 5.2 Formulate Conclusion

Based on the documented test results and exceptions, formulate a conclusion on the effectiveness of the change control process for the audit period. Conclude whether the controls are operating as designed, or if deficiencies were identified that need to be addressed.
                """,
                "additional_description": """
                The files to process are:
                - REQ-3096305_(2).png
                - SPR23-000395_(1).pdf
                - SPR24-000098.pdf
                - SPR24-000150_(1).pdf
                - SPR24-000196.pdf
                - CO2 Test Worksheet- Example.xlsx

                CO2 Test Worksheet- Example.xlsx is the final report template, you have to generate the final report named: audit_analysis_report.xlsx based on the template.
                """,
                "tools": ["advanced_data_analysis_tool"],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
        ],
    },
}


GHCO_DEKKO_CO2_CONTROL_MULTIPLE = {
    "GHCO-DEKKO-CO2-CONTROL-MULTIPLE": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK**
        """,
        # Agent control configuration
        "agent_control": {
            "name": "Supervisor Agent for GHCO DEKKO CO2 Control",
            "edges": [
                {"source": 0, "target": 1, "condition": ""},
                {"source": 1, "target": 2, "condition": ""},
                {"source": 2, "target": 3, "condition": ""},
            ],
        },
        # Agent actions configuration
        "agent_actions": [
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "credentials": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "object",
                            "example": """{"google_token": "---google-token---"}""",
                            "description": "Key-value credential map available to tools",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "credentials": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "object",
                            "example": """{"google_token": "---google-token---"}""",
                            "description": "Key-value credential map available to tools",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "credentials": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "object",
                            "example": """{"google_token": "---google-token---"}""",
                            "description": "Key-value credential map available to tools",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
                        },
                    },
                },
            },
            {
                "action_prototype_name": "SupervisorAgent",
                "order": 0,
                "control_variables": {},
                "reference_variables": {},
                "independent_variable_schema": {
                    "credentials": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "object",
                            "example": """{"google_token": "---google-token---"}""",
                            "description": "Key-value credential map available to tools",
                        },
                    },
                    "task_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Check if there are any emails related with REQ-3114054",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
                        },
                    },
                    "additional_description": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
                        },
                    },
                    "model_provider": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "openai",
                            "description": "The model provider to use for the supervisor agent",
                        },
                    },
                    "model_name": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "string",
                            "example": "gpt-4.1",
                            "description": "The model name to use for the supervisor agent",
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
                "credentials": {},
                "task_description": """
                You are a GHCO Request Agent that creates audit requests for Business Unit.

                Your tasks:
                Create requests for one Business Unit and extract its tracking ID, ensure the request is created successfully.
                When creating requests:
                - Use the provided template and fill in the Application name dynamically
                - Extract and record tracking IDs for each request
                - Create requests for all Application in the list

                Steps to reach I.T. Assessments page:
                    (1) Navigate to 'Filter' input field on the left.
                    (2) Input text 'I.T. Assessments (2022 - forward)' to field 'Filter'.
                    (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"
                    Under the first column Assessment of the table, you can find the clickable cells for the target assessment
                    Find the one for the target assessment and click it.
                    After going into the specific page, there is a button Add New, click it to create a new request.

                Click Save button.
                Record the Tracking ID.
                You must find the tracking id on the page.
                After clicking the Save button, an Tracking ID will be generated, it is in the format REQ-xxxxxxx, where xxxxxxx is a series of numbers.
                Tracking ID:

                Expected Output: Output the Tracking ID from the application, outputted as REQ-xxxxxxx, Do not make up the ID if you can't find it, you can output you are unable to find the ID.

                You can use the username: AIAuditor and password: YfDrK0ljMzmFLB
                """,
                "additional_description": """
                Target Assessment: 2025 (Q4) - Cable Division:Cable ONE



                Make sure all the information is filled correctly before you click Save button, otherwise the request will not be created successfully, a popup will show the error message.

                Template for giving browser_agent a task:
                    <template>
                    Home page: "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
                    Target Business Unit: "Cable Division:Cable ONE"
                    Fill the form with the following 6 entries:
                    {{
                        "Test Period": "Interim" Note: Only select Interim from multi-select options.
                        "Control Area": select "CO2* - Operational Change Control" then click OK.
                        "Request Description": filled with "***INTERIM REQUEST***
                For InforLX &MRO applications, databases and OS

                Provide a listing of all changes implemented from 1/1/2024 to 8/1/2024 or thereabouts (including the supporting infrastructure, i.e., operating system and databases). Capture screenshots of the commands/scripts used, as well as the system, from which this listing is generated.""
                        "Date Due": <Two weeks from today (date are usually in MM/DD/YYYY format)>
                        "Requested by": "agent, AI Auditor" (You need to search the name using the UI, click on Search before selecting the name)
                        "BU Contact(s)": "agent, AI BU" (You need to search the name using the UI, click on Save before selecting the name)
                    }}
                    </template>
                """,
                "tools": ["browser_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": """
                Your AI Email Agent, your task is to send the Tracking ID base on previous result and pause the execution to wait for evidence to get uploaded on Tracking ID. When resume you can assume that the evidence is uploaded and this task is completed.
                User generic_gmail_agent_tool to send email in format:

                Subject: GHCO Request Created - [Tracking ID]
                Body:
                Dear [Recipient Name],

                The GHCO request has been created successfully. The Tracking ID is [Tracking ID]. Please proceed with uploading the necessary evidence to this request.

                Warm Regards,
                AI Auditor

                Request pause after sending email as i want to wait for evidence to get uploaded on Tracking ID, you can assume that the evidence is uploaded when resume and this task is completed.
                """,
                "additional_description": f"Send email to shawn@alltrue.ai and token used for email tool is {GOOGLE_CREDENTIALS}",
                "tools": ["generic_gmail_agent_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": """
                On resume, consider the task is completed.

                You are a GHCO Request Receiver Agent that validates the requests created by GHCO Request Agent and downloads all evidence files uploaded to those requests, regardless of the quantity.

                Your tasks:

                Navigate to the request using the tracking ID provided by the GHCO Request Agent. Here are the steps where you can find the old requests:

                Steps to Reach and Open the Request
                1. Navigate to the 'Filter' input field on the left.
                2. Input text 'I.T. Assessments (2022 - forward)' into the field.
                3. Click "I.T. Assessments (2022 - forward)" under "ITGC 2024".
                4. Click on Target Assessment
                5. Find the specific Tracking ID on the page and click on it to open the request details page.
                5. Read the request description and locate the section containing the evidence files (e.g., "interim evidence files" or equivalent attachment field).

                Evidence File Download Plan (Mandatory Iterative Download)
                1. Count Files: Create a file name list of all evidence files attached to the request.
                2. Execute Download Loop: Initiate a download process that continues until the count of remaining files to be downloaded is zero.
                3. Loop Condition: While the number of files available for download is greater than zero:
                4. Select the next available file from the list.
                5. Download the file to a local folder.
                6. Verify the file has successfully saved and is complete.
                7. Remove the downloaded file from the list of 'files to process' (or decrement the count).
                8. Error Handling: Implement a retry mechanism within the loop for any file that fails to download or verify on the first attempt (retry up to 3 times per file).
                You can stop if you cannot find the request using the provided Tracking ID on the specified page. Do not navigate to subsequent pages to search for the request.

                Expected Output: Name of the files downloaded, and the Upload Date of the files

                You can use the username: AIAuditor and password: YfDrK0ljMzmFLB

                Request Pause after downloading all evidence files.
                """,
                "additional_description": """
                Home Page: https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx

                Target Assessment: 2025 (Q4) - Cable Division:Cable ONE

                The tracking ID should be referred from Request Agent or Email Agent.
                """,
                "tools": ["browser_tool"],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
            {
                "credentials": {},
                "task_description": """

                # Manual for IT Change Control Audit Testing

                ## 1.0 Objective

                The purpose of this procedure is to provide a standardized set of instructions for testing the effectiveness of IT change management controls. This process ensures that all changes to in-scope systems are properly requested, tested, approved, and implemented, thereby maintaining the integrity of the IT environment.

                ## 2.0 Procedure Overview

                The audit process consists of three primary phases:

                1.  **Population Gathering & Sampling:** Obtaining a complete and accurate list of all changes within the audit period and selecting a sample for testing.
                2.  **Detailed Evidence Testing:** Examining the documentation for each sampled change to verify that key control steps were followed.
                3.  **Analysis & Conclusion:** Documenting the results and identifying any exceptions or control weaknesses.

                ---

                ## 3.0 Phase 1: Population Gathering & Sampling

                ### 3.1 Define Scope and Request Population

                1.  **Initiate Request:** Formally request a complete listing of all changes for the target application (e.g., BPIX) and a specific audit period (e.g., January 1st to August 1st).
                2.  **Request Supporting Evidence:** In the request, specify that two forms of evidence are required from the system owner:
                    * A screenshot of the system query or filters used to generate the list. This validates the completeness of the population.
                    * The complete change ticket documentation (e.g., PDF files) for every change on the generated list.

                ### 3.2 Validate Population and Select Sample

                1.  **Verify Filters:** Upon receipt, review the screenshot of the filters. Ensure the criteria correctly match the audit scope.
                    * **Guidance & Example:** The filters should clearly define the population. For instance, the query should show filters for:
                        * `Status: Completed`
                        * `Scope: In Scope (SOX)`
                        * `Year: [Current Audit Year]`

                2.  **Determine Sample Size:** Count the total number of changes in the validated population. Based on your organization's audit methodology and the population size, determine the appropriate sample size for testing.
                    * **Guidance & Example:** For a small population (e.g., 4 changes), a sample of 2 might be sufficient for interim testing, with a plan to test additional changes later in the year.

                ---

                ## 4.0 Phase 2: Detailed Evidence Testing

                For each change ticket selected in your sample, perform the following steps to extract evidence from the source document (PDF) and record it in the destination document (Excel Testing Table).

                ### 4.1 Data Extraction and Recording

                Use the following table as a guide to map information from the change ticket PDF to your Excel testing worksheet.

                [
                {
                "excel_field": "Change Ticket #",
                "how_to_find_in_pdf": "Locate the unique Project or Request Number. This is typically in the document header. Example: 'SPRC2-XXXXXX'.",
                "purpose_rationale": "Serves as the unique identifier for the change being tested."
                },
                {
                "excel_field": "Change Type",
                "how_to_find_in_pdf": "Find the 'Type' field, usually under a 'Project Information' section. Example: 'Project Request'.",
                "purpose_rationale": "Categorizes the nature of the change."
                },
                {
                "excel_field": "System Impacted",
                "how_to_find_in_pdf": "May need to be inferred from the 'Name of Project' field or technical object descriptions within the ticket. Example: 'BPIX'.",
                "purpose_rationale": "Identifies the specific application or system being modified."
                },
                {
                "excel_field": "Description of change",
                "how_to_find_in_pdf": "Copy the text from the 'Name of Project' or a similar summary field.",
                "purpose_rationale": "Provides a clear, concise summary of the change's purpose."
                },
                {
                "excel_field": "Developer",
                "how_to_find_in_pdf": "Identify the name listed in the 'Suggested Developer' or 'IT Resources' field.",
                "purpose_rationale": "Records who was responsible for the technical development of the change."
                },
                {
                "excel_field": "Evidence of testing?",
                "how_to_find_in_pdf": "Look for a section titled 'Analyst Evaluation' or similar. If the developer has documented their testing steps and results, record 'Yes.'",
                "purpose_rationale": "Confirms that testing was performed. Developer-level unit testing is the minimum requirement."
                },
                {
                "excel_field": "Change Tester",
                "how_to_find_in_pdf": "Identify the author of the 'Analyst Evaluation' section. Cross-reference with the 'Testing Validation' section.",
                "purpose_rationale": "Documents who performed the testing. Check for fields like 'Does anyone else need to test these changes?' to see if testing was limited to the developer."
                },
                {
                "excel_field": "Testing Date",
                "how_to_find_in_pdf": "In the 'Phase Tracking' table at the end of the document, find the 'Completed' date for the 'Analyst Evaluation' activity.",
                "purpose_rationale": "Establishes the date when testing was successfully completed."
                },
                {
                "excel_field": "Pre-production approver",
                "how_to_find_in_pdf": "In the 'Phase Tracking' table, find the name associated with the 'IT Review' or equivalent pre-approval activity.",
                "purpose_rationale": "Identifies the manager or lead who formally approved the change to proceed."
                },
                {
                "excel_field": "Approval date",
                "how_to_find_in_pdf": "In the 'Phase Tracking' table, find the 'Completed' date for the 'IT Review' activity.",
                "purpose_rationale": "Records the date of the formal, pre-implementation approval."
                },
                {
                "excel_field": "Migration to Production by",
                "how_to_find_in_pdf": "In the 'Phase Tracking' table, find the name associated with the 'Project Installation' or deployment activity.",
                "purpose_rationale": "Identifies the individual who moved the code into the live production environment."
                },
                {
                "excel_field": "Migration date",
                "how_to_find_in_pdf": "In the 'Phase Tracking' table, find the 'Completed' date for the 'Project Installation' activity.",
                "purpose_rationale": "Marks the specific date the change went live and became active for users."
                }
                ]

                ---

                ## 5.0 Phase 3: Analysis & Conclusion

                After recording the data for all samples, analyze the findings to form a conclusion.

                ### 5.1 Identify and Document Exceptions

                Review the completed testing table for potential control issues or deviations from standard procedure.

                1.  **Check for Segregation of Duties (SoD) Conflicts:**
                    * **Situation:** Compare the `Developer`, `Change Tester`, and `Migration to Production by` fields. If the same person performed development and migration to production, an SoD conflict exists.
                    * **Correspondence/Action:** Document this in the "Exceptions" column. If this is a known risk in a small IT shop, reference any mitigating controls that are tested elsewhere. *Example Note: "Developer also migrated change to production. This is a known issue mitigated by post-implementation reviews."*

                2.  **Verify Process Adherence:**
                    * **Situation:** Compare the key dates (`Approval date`, `Testing Date`, `Migration date`). Does the sequence make sense? For example, approval should ideally occur before migration.
                    * **Correspondence/Action:** Document the observed process. *Example Note: "The process shows that formal approval is performed prior to development and testing, which is the established workflow for this business unit."*

                3.  **Confirm Testing Requirements:**
                    * **Situation:** Was testing performed by someone other than the developer?
                    * **Correspondence/Action:** If not, confirm that the change ticket did not require it. *Example Note: "Per the 'Testing Validation' section of the ticket, no testing was required beyond the developer's unit test."*

                ### 5.2 Formulate Conclusion

                Based on the documented test results and exceptions, formulate a conclusion on the effectiveness of the change control process for the audit period. Conclude whether the controls are operating as designed, or if deficiencies were identified that need to be addressed.
                """,
                "additional_description": """
                Base on the files you downloaded, fill the data in the CO2 Test Worksheet- Example.xlsx and generate the final report named: audit_analysis_report.xlsx based on the template.

                CO2 Test Worksheet- Example.xlsx is the final report template, you have to generate the final report named: audit_analysis_report.xlsx based on the template.
                """,
                "tools": ["advanced_data_analysis_tool"],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
        ],
    },
}
