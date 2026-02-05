from test_suite.credential import GOOGLE_CREDENTIALS

GHCO_CO2_CONTROL = {
    "GHCO-CO2-CONTROL": {
        "setting_type": "Multiple Actions",
        "control_instruction": """
        **SKIP COMPLIANCE CHECK**
        """,
        # Agent control configuration
        "agent_control": {
            "name": "Supervisor Agent for GHCO CO2 Control",
            "edges": [
                {"source": 0, "target": 1, "condition": ""},
                {"source": 1, "target": 2, "condition": ""},
                {"source": 2, "target": 3, "condition": ""},
                {"source": 3, "target": 4, "condition": ""},
                {"source": 4, "target": 5, "condition": ""},
                {"source": 5, "target": 6, "condition": ""},
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
                "order": 1,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                "order": 2,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                "order": 3,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                "order": 4,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                "order": 5,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                "order": 6,
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
                            "example": "Send your findings to shawn@alltrue.ai",
                            "description": "Additional context or output requirements for the supervisor agent",
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
                    "tools": {
                        "value_type": "args",
                        "args_schema": {
                            "type": "array",
                            "example": """["generic_gmail_agent_tool"]""",
                            "description": "List of tool ids allowed for the supervisor agent",
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
                - Use the provided template and fill in the software name dynamically
                - Extract and record tracking IDs for each request
                - Create requests for all software in the list

                Steps to reach I.T. Assessments page:
                    (1) Navigate to 'Filter' input field on the left.
                    (2) Input text 'I.T. Assessments (2022 - forward)' to field 'Filter'.
                    (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"
                    Under the first column Assessment of the table, you can find the clickable cells for different business unit. The names are in <Year> (<Season>) - <Business Unit>
                    Find the one for the target business unit and click it.
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
                Make sure all the information is filled correctly before you click Save button, otherwise the request will not be created successfully, a popup will show the error message.

                Template for giving browser_agent a task:
                    <template>
                    Home page: "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
                    Target Business Unit: "Cable Division:Cable ONE"
                    Fill the form with the following 6 entries:
                    {{
                        "Test Period": "Interim" Note: Only select Interim from multi-select options.
                        "Control Area": "CO2* - Operational Change Control"
                        "Request Description":
                        "Change Management - DRM, Mulesoft, Oracle ERP, Oracle EPM/ePBCS/PCMCS Application, Database and Operating System

                        Provide a listing of all changes implemented from KFCS (KSS Jira project) from 1/1/2024 through 5/31/2024
                        Note:
                        1) Included the supporting infrastructure (i.e. operating system and databases) changes
                        2) Capture screenshots of the commands/scripts used, as well as the system, from which this listing is generated."
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
                "additional_description": f"Send email to segalinc@alltrue.ai and token used for email tool is {GOOGLE_CREDENTIALS}",
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
                4. Click on "2025 (Q4) - Cable Division:Cable ONE".
                5. Find the specific Tracking ID on the page and click on it to open the request details page.
                5. Read the request description and locate the section containing the evidence files (e.g., "interim evidence files" or equivalent attachment field).

                Evidence File Download Plan (Mandatory Iterative Download)
                1. Count Files: Create a list of all evidence files attached to the request and store in a list.
                2. Execute Download Loop: Initiate a download process that continues until the count of remaining files to be downloaded is zero.
                3. Loop Condition: While the number of files available for download is greater than zero:
                4. Select the next available file from the list.
                5. Download the file to a local folder.
                6. Verify the file has successfully saved and is complete.
                7. Remove the downloaded file from the list of 'files to process' (or decrement the count).
                8. Error Handling: Implement a retry mechanism within the loop for any file that fails to download or verify on the first attempt (retry up to 3 times per file).
                You can stop if you cannot find the request using the provided Tracking ID on the specified page. Do not navigate to subsequent pages to search for the request.

                Expected Output: Name of the files downloaded in formatted manner and validation from agent that all requests created by GHCO Request Agent is successfully located along with tracking ID

                You can use the username: AIAuditor and password: YfDrK0ljMzmFLB

                Request Pause after downloading all evidence files.
                """,
                "additional_description": """
                Home Page: https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx
                Target Business Unit: Cable Division:Cable ONE
                The tracking ID should be referred from Request Agent or Email Agent.
                """,
                "tools": ["browser_tool"],
                "model_provider": "openai",
                "model_name": "gpt-4.1",
            },
            {
                "credentials": {},
                "task_description": """
                If you are resuming, consider this task is done.

                You are an Advanced Data Analysis Agent. Your task is to analyze the sample size for auditing purposes.
                In previous step, you downloaded all evidence files uploaded to the requests created by GHCO Request Agent. Now, you need to analyze the sample size of software usage based on the provided data.

                You need to calculate the total number of records for 4 different categories from the input data:
                Do not count header row if there is one.
                1. Stories: Locate the data relevant to KFCS Stories for Deployment and calculate the total number of records. The Column in file, Type Maintenance is same as Type Story, you need to include both.
                2. Maintenance: Locate the data relevant to KFCS Maintenance and calculate the total number of records.
                3. KRFCs (SOX Impact): Locate the data relevant to KRFCs (SOX Impact) and calculate the total number of records, make sure SOX Impact is Yes.
                4. Oracle Patches: Locate the data relevant to KFCS stories for patches and calculate the total number of records.

                The data might be in different files, you need to read all files and calculate the total number of records for each category.
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
                Expected Output:

                The output should tell me what the count was in each file you analyzed, for example:

                File: File Name,  File Name ...
                Stories: Count 1, Count 2 ...
                Maintenance: Count 1, Count 2 ...
                KRFCs (SOX Impact): Count 1, Count 2 ...
                Oracle Patches: Count 1, Count 2 ...
                Total: Sum of column, Sum of column
                Total Sum = Sum 1, Sum 2 ...

                The sum must be done together for all categories, and then frequency mapping and sample size mapping must be done based on the total sum.
                For example: If the total sum is 300, then the frequency is "Multiple Times Per Day" and the sample size is 20.
                You can use the Advanced Data Analysis Tool to help you analyze the data and generate the result, the filenames should only include the name of files, not the path
                The final goal is to output one number which is the sample size for audit purpose based on the analysis you did.

                Go to pause.
                """,
                "additional_description": "",
                "tools": ["advanced_data_analysis_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": """
                If you are resuming, consider this task is done.

                You are an Advanced Data Analysis Agent. Based on the final sample size you calculated in previous step.
                Generate a a totally random sample from the data you downloaded from the GHCO system.
                The sample must contain a data point from each category.
                You can use the Advanced Data Analysis Tool to help you generate the sample, the filenames should only include the name of files, not the path
                and output should be text format only. Do not generate any files. Just output plain text.

                Expected Output:
                Write a descriptive request for the sample you generated for the Business to provide proof of the data mentioned in the sample. You must be detailed and based
                on the nature of the system the Request must be very specific about what the Business needs to provide as proof.

                Go to pause.
                """,
                "additional_description": "",
                "tools": ["advanced_data_analysis_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
            {
                "credentials": {},
                "task_description": """
                If you are resuming, consider this task is done.

                You are a GHCO Request Agent that creates audit requests for Business Unit.

                Your tasks:
                Create requests for one Business Unit and extract its tracking ID, ensure the request is created successfully.
                When creating requests:
                - Use the provided template and fill in the software name dynamically
                - Extract and record tracking IDs for each request
                - Create requests for all software in the list

                Steps to reach I.T. Assessments page:
                    (1) Navigate to 'Filter' input field on the left.
                    (2) Input text 'I.T. Assessments (2022 - forward)' to field 'Filter'.
                    (3) Click "I.T. Assessments (2022 - forward)" under "ITGC 2024"
                    Under the first column Assessment of the table, you can find the clickable cells for different business unit. The names are in <Year> (<Season>) - <Business Unit>
                    Find the one for the target business unit and click it.
                    After going into the specific page, there is a button Add New, click it to create a new request.

                Click Save button.
                Record the Tracking ID.
                You must find the tracking id on the page.
                After clicking the Save button, an Tracking ID will be generated, it is in the format REQ-xxxxxxx, where xxxxxxx is a series of numbers.
                Tracking ID:

                Expected Output: Output the Tracking ID from the application, outputted as REQ-xxxxxxx, Do not make up the ID if you can't find it, you can output you are unable to find the ID.

                You can use the username: AIAuditor and password: YfDrK0ljMzmFLB
                Go to pause.
                """,
                "additional_description": """
                Make sure all the information is filled correctly before you click Save button, otherwise the request will not be created successfully, a popup will show the error message.

                Template for giving browser_agent a task:
                    <template>
                    Home page: "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
                    Target Business Unit: "Cable Division:Cable ONE"
                    Fill the form with the following 6 entries:
                    {{
                        "Test Period": "Interim" Note: Only select Interim from multi-select options.
                        "Control Area": "CO2* - Operational Change Control" (You need to search the name using the UI, click on Search before selecting the name)
                        "Request Description": "Change Management Interim - Oracle ERP, Oracle EPM/ePBCS, DRM, and Mulesoft

                        Please provide supporting evidence for the Kaplan Inc. Oracle ERP, Oracle EPM/ePBCS, DRM, and Mulesoft sample selections:

                        [The random sample you generated in previous step]

                        "Date Due": <Two weeks from today (date are usually in MM/DD/YYYY format)>
                        "Requested by": "agent, AI Auditor" (You need to search the name using the UI, click on Search before selecting the name)
                        "BU Contact(s)": "agent, AI BU" (You need to search the name using the UI, click on Search before selecting the name)
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
                You are a GHCO Request Analyzer Agent that analyzes the requests created by GHCO Request Agent,

                Your tasks:
                Search the and close the requests created by GHCO Request Agent. Here are the steps where you can find the old requests:

                1. On the Home Page, directly search the request ids created by GHCO Request Agent, you can find the request ids from previous step.
                2. Open each request and Edit the request.
                3. Change the Requested Closed? field to Yes.
                4. Click Save button to save the changes.

                After you close all the requests, output the request ids you closed.

                After closing the request, write an email in the format:

                Subject: GHCO Requests Closed - [Tracking ID 1, Tracking ID 2, ...]

                Dear [Recipient Name],

                The GHCO requests have been closed successfully. The Tracking IDs are [Tracking ID 1, Tracking ID 2, ...].

                Warm Regards,
                AI Auditor
                """,
                "additional_description": f"Send email to segalinc@alltrue.ai and token used for email tool is {GOOGLE_CREDENTIALS}, the home page is https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx and you can use the username: AIAuditor and password: YfDrK0ljMzmFLB",
                "tools": ["browser_tool", "generic_gmail_agent_tool"],
                "model_provider": "gemini",
                "model_name": "gemini-2.5-flash",
            },
        ],
    },
}
