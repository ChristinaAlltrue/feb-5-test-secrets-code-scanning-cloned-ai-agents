# Test settings for Custom Questionnaire Assistant agent
# Note: You may need to add actual credentials or URLs to test_suite/credential.py
from test_suite.credential import GOOGLE_CREDENTIALS

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** Answer all questions in the spreadsheet using information from the context document.
        Extract questions from the sheet and provide accurate answers based on the context.
        Create a new Excel file with question-answer pairs.
        """,
        "entity": {
            "google_token": GOOGLE_CREDENTIALS,
            "sheet_name": "Shawn-Questionnaire-Question-sheet",
            "context_document_name": "Shawn-Questionnaire-context",
            "goal": """
            Base on the content, answer all questions found in the spreadsheet.
            """,
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {},
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "google_token": {
                "args_schema": {
                    "type": "string",
                    "example": "---token---",
                    "description": "The Google token to access the Google Drive",
                }
            },
            "sheet_name": {
                "args_schema": {
                    "type": "string",
                    "example": "Shawn-Questionnaire-Question-sheet",
                    "description": "The sheet name of the .xlsx file. The name is expected to be a public URL that can be accessed without authentication",
                }
            },
            "context_document_name": {
                "args_schema": {
                    "type": "string",
                    "example": "Shawn-Questionnaire-context",
                    "description": "Document name that provides context for the agent to fill the spreadsheet. The name is expected to be a public URL that can be accessed without authentication",
                }
            },
            "goal": {
                "args_schema": {
                    "type": "string",
                    "example": "Using the company policy document, answer all questions found in the spreadsheet",
                    "description": "The goal of the agent. Natural language description of what the user wants the agent to do with the spreadsheet",
                }
            },
        },
    },
}
