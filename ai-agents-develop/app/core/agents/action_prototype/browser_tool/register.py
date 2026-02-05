from app.core.agents.action_prototype.browser_tool.action import (
    browser_tool as browser_playwright_tool,
)
from app.core.agents.action_prototype.browser_tool.schema import BrowserToolParams
from app.core.agents.action_prototype.bundles import ToolBundle

browser_tool = ToolBundle.from_function(
    browser_playwright_tool,
    tool_id=f"browser_tool",
    tool_display_name="Browser Tool",
    description="Browser based tool that uses Playwright and MCP to perform tasks on websites, supports authentication and basic browser tasks.",
    parameters_model=BrowserToolParams,
    takes_ctx=True,
    max_retries=10,
    default_model="Gemini 2.5 Flash",
)

browser_tool.register()
