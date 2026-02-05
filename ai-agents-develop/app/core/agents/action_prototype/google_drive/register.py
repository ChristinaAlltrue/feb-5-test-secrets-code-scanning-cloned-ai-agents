from app.core.agents.action_prototype.bundles import ToolBundle
from app.core.agents.action_prototype.google_drive.action import google_drive_mcp_tool
from app.core.agents.action_prototype.google_drive.schema import GoogleDriveMCPParams

# =====Register Tool =====
TOOL_ID = google_drive_mcp_tool.__name__
TOOL_DISPLAY_NAME = "Google Drive"
TOOL_DESCRIPTION = "A tool to interact with Google Drive to find and download files."

google_drive_mcp = ToolBundle.from_function(
    google_drive_mcp_tool,
    tool_id=TOOL_ID,
    tool_display_name=TOOL_DISPLAY_NAME,
    description=TOOL_DESCRIPTION,
    parameters_model=GoogleDriveMCPParams,
    takes_ctx=True,
    max_retries=10,
    default_model="GPT-5.1 Instant",
)

google_drive_mcp.register()
