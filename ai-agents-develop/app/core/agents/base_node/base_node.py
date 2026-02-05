from abc import ABC

from pydantic import Field
from pydantic_graph import BaseNode

from app.core.graph.state.state import State

SYSTEM_PROMPT_TEMPLATE = """
{customized_system_prompt}

**IMPORTANT**
If original instruction has any conflict with the extra instructions, you should follow the extra instructions.
"""

USER_PROMPT_TEMPLATE = """
{original_user_prompt}

Extra Instructions: {extra_instructions}
"""


class AgentBaseNode(BaseNode[State], ABC):
    resume: bool = Field(default=False)
    extra_instructions: str = Field(default="")

    @staticmethod
    def complete_system_prompt(customized_system_prompt: str) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            customized_system_prompt=customized_system_prompt
        )

    @staticmethod
    def complete_user_prompt(original_user_prompt: str, extra_instructions: str) -> str:
        return USER_PROMPT_TEMPLATE.format(
            original_user_prompt=original_user_prompt,
            extra_instructions=extra_instructions,
        )
