from app.core.agents.action_prototype.bundles import ToolBundle
from app.core.agents.action_prototype.github_mcp.action import github_mcp_tool
from app.core.agents.action_prototype.github_mcp.schema import GithubMCPToolParams

TOOL_ID = github_mcp_tool.__name__
TOOL_DISPLAY_NAME = "Github MCP"
TOOL_DESCRIPTION = "GitHub MCP Tool is a utility that helps manage and automate interactions with GitHub repositories, including cloning, updating, and maintaining multiple projects efficiently. It streamlines workflow management for developers working across several repositories."

github_mcp = ToolBundle.from_function(
    github_mcp_tool,
    tool_id=TOOL_ID,
    tool_display_name=TOOL_DISPLAY_NAME,
    description=TOOL_DESCRIPTION,
    parameters_model=GithubMCPToolParams,
    takes_ctx=True,
    max_retries=10,
    default_model="GPT-5.1 Instant",
)

github_mcp.register()
