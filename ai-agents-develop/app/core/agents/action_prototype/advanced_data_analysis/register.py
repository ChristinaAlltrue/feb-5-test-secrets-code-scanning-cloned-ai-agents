from app.core.agents.action_prototype.advanced_data_analysis.action import (
    advanced_data_analysis_tool,
)
from app.core.agents.action_prototype.advanced_data_analysis.schema import (
    AdvancedDataAnalysisToolParams,
)
from app.core.agents.action_prototype.bundles import ToolBundle

# =====Register Tool =====
TOOL_ID = advanced_data_analysis_tool.__name__
TOOL_DISPLAY_NAME = "Advanced Data Analysis"
TOOL_DESCRIPTION = "An AI-powered sandbox for data analysis, visualization, file manipulation, and code execution."

advanced_data_analysis = ToolBundle.from_function(
    advanced_data_analysis_tool,
    tool_id=TOOL_ID,
    tool_display_name=TOOL_DISPLAY_NAME,
    description=TOOL_DESCRIPTION,
    parameters_model=AdvancedDataAnalysisToolParams,
    takes_ctx=True,
    max_retries=10,
    default_model="GPT-5.1 Thinking",
    allowed_model_criteria={"provider": ["openai"], "capabilities": ["reasoning"]},
)

advanced_data_analysis.register()
