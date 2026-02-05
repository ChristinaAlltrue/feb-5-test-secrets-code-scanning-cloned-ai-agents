# Test settings for Custom Questionnaire Assistant agent
# Note: You may need to add actual credentials or URLs to test_suite/credential.py

TEST_SETTINGS = {
    "test1": {
        "control_instruction": """
        Answer all questions in the spreadsheet using information from the context document.
        Extract questions from the sheet and provide accurate answers based on the context.
        Create a new Excel file with question-answer pairs.
        """,
        "entity": {
            "sheet_url": "https://docs.google.com/spreadsheets/d/1OW4QSCQEQ4eHn8OEKvrFpTr6Pt-H8tpHWCHfZaFVCY0/export?format=xlsx",
            "context_document_url": "https://docs.google.com/document/d/1s3ZZv4cVv-I4XYXRjCjwG95L-fdAGTci9GALT1nuQtM/export?format=txt",
            "goal": """
            Base on the document, answer all questions found in the spreadsheet.
            """,
        },
        # Example of control variables (PrimitiveDeps)
        "control_variables": {},
        # Example of independent variables (ArgsDeps) - these can override schema defaults
        "independent_variables": {
            "sheet_url": {
                "args_schema": {
                    "type": "string",
                    "example": "https://example.com/spreadsheet.xlsx",
                    "description": "The sheet URL of the .xlsx file. The URL is expected to be a public URL that can be accessed without authentication",
                }
            },
            "context_document_url": {
                "args_schema": {
                    "type": "string",
                    "example": "https://example.com/company_policy.pdf",
                    "description": "Document URL that provides context for the agent to fill the spreadsheet. The URL is expected to be a public URL that can be accessed without authentication",
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
