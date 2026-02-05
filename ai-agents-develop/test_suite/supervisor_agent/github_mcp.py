from test_suite.credential import GITHUB_TOKEN

GITHUB_MCP_TOOL_TEST = {
    "Github MCP": {
        "control_instruction": """
        **SKIP COMPLIANCE CHECK** .
        """,
        "entity": {
            "credentials": {},
            "task_description": "Who is the author of this PR? https://github.com/pydantic/pydantic-ai/pull/3164 and the date it was merged?",
            "additional_description": f"You can use the following github token {GITHUB_TOKEN}",
            # Tools available to the supervisor (must match TOOLS_REGISTRY keys)
            "tools": ["github_mcp_tool"],
            "model_provider": "gemini",
            "model_name": "gemini-2.5-flash",
        },
        # Control variables (PrimitiveDeps)
        "control_variables": {},
        # Independent variables (ArgsDeps) inferred from schema
        "independent_variables": {
            "task_description": {
                "args_schema": {
                    "type": "string",
                    "example": "Search inbox for the latest message from John and summarize it",
                    "description": "Primary task description for the supervisor agent",
                }
            },
            "additional_description": {
                "args_schema": {
                    "type": "string",
                    "example": "Email subject, recipients, and send confirmation",
                    "description": "Additional context or output requirements",
                }
            },
            "tools": {
                "args_schema": {
                    "type": "array",
                    "example": """["generic_gmail_agent_tool"]""",
                    "description": "List of tool ids allowed for the supervisor agent",
                }
            },
            "credentials": {
                "args_schema": {
                    "type": "object",
                    "example": """{"google_token": "---google-token---"}""",
                    "description": "Key-value credential map available to tools",
                }
            },
            "model_provider": {
                "args_schema": {
                    "type": "string",
                    "example": "openai",
                    "description": "The model provider to use for the supervisor agent",
                }
            },
            "model_name": {
                "args_schema": {
                    "type": "string",
                    "example": "gpt-4.1",
                    "description": "The model name to use for the supervisor agent",
                }
            },
        },
    },
}
