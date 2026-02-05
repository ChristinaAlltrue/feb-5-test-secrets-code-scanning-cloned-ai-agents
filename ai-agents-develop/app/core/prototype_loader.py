# Force loading of all prototypes to trigger the registration. Check  app/core/registry.py
from app.core.agents.action_prototype.advanced_data_analysis import (  # noqa: F401 # type: ignore
    register as advanced_data_analysis_register,
)
from app.core.agents.action_prototype.audit_analysis_agent import (  # noqa: F401 # type: ignore
    register as audit_analysis_agent_register,
)
from app.core.agents.action_prototype.audit_analysis_browser_agent import (  # noqa: F401 # type: ignore
    register as audit_analysis_browser_agent_register,
)
from app.core.agents.action_prototype.audit_analysis_connected_agents import (  # noqa: F401 # type: ignore
    register as audit_analysis_connected_agents_register,
)
from app.core.agents.action_prototype.audit_analysis_connected_agents_part2 import (  # noqa: F401 # type: ignore
    register as audit_analysis_connected_agents_part2_register,
)
from app.core.agents.action_prototype.audit_file_collection_agent import (  # noqa: F401 # type: ignore
    register as audit_file_collection_agent_register,
)
from app.core.agents.action_prototype.browser_tool import (  # noqa: F401 # type: ignore
    register as browser_tool_register,
)
from app.core.agents.action_prototype.counter import (  # noqa: F401 # type: ignore
    register as counter_register,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant import (  # noqa: F401 # type: ignore
    register as custom_questionnaire_assistant_register,
)
from app.core.agents.action_prototype.custom_questionnaire_assistant_v2 import (  # noqa: F401 # type: ignore
    register as custom_questionnaire_assistant_v2_register,
)
from app.core.agents.action_prototype.file_inspection import (  # noqa: F401 # type: ignore
    register as sheet_compare_register,
)
from app.core.agents.action_prototype.generic_auditor_agent import (  # noqa: F401 # type: ignore
    register as generic_auditor_agent_register,
)
from app.core.agents.action_prototype.generic_gmail_agent import (  # noqa: F401 # type: ignore
    register as generic_gmail_agent_register,
)
from app.core.agents.action_prototype.GHCO_auditor import (  # noqa: F401 # type: ignore
    register as ghco_auditor_register,
)
from app.core.agents.action_prototype.github_auditor import (  # noqa: F401 # type: ignore
    register as github_auditor_register,
)
from app.core.agents.action_prototype.github_auditor_with_screenshot import (  # noqa: F401 # type: ignore
    register as github_auditor_with_screenshot_register,
)
from app.core.agents.action_prototype.github_mcp import (  # noqa: F401 # type: ignore
    register as github_mcp_register,
)
from app.core.agents.action_prototype.gmail_listener import (  # noqa: F401 # type: ignore
    register as gmail_listener_register,
)
from app.core.agents.action_prototype.google_drive import (  # noqa: F401 # type: ignore
    register as googler_drive_register,
)
from app.core.agents.action_prototype.login import (  # noqa: F401 # type: ignore
    register as login_register,
)
from app.core.agents.action_prototype.longterm_memory_agent import (  # noqa: F401 # type: ignore
    register as longterm_memory_agent_register,
)
from app.core.agents.action_prototype.navigation import (  # noqa: F401 # type: ignore
    register as navigation_register,
)
from app.core.agents.action_prototype.pause import (  # noqa: F401 # type: ignore
    register as pause_register,
)
from app.core.agents.action_prototype.sample import (  # noqa: F401 # type: ignore
    register as sample_register,
)
from app.core.agents.action_prototype.sample_generic_action import (  # noqa: F401 # type: ignore
    register as sample_generic_action_register,
)
from app.core.agents.action_prototype.screenshot import (  # noqa: F401 # type: ignore
    register as screenshot_register,
)
from app.core.agents.action_prototype.start import (  # noqa: F401 # type: ignore
    register as start_register,
)
from app.core.agents.action_prototype.supervisor_agent import (  # noqa: F401 # type: ignore
    register as supervisor_agent_register,
)
