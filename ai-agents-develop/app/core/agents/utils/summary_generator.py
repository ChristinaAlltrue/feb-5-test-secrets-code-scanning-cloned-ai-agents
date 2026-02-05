from typing import Any

from pydantic_ai import Agent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

SUMMARY_AGENT_PROMPT = """
The user will provide LLM output. Write a concise, human-readable summary of the entire content in no more than 250 words.
"""


async def generate_summary(output: Any) -> str:
    """
    Output of action execution, its usually a dict or string
    """
    output_string = str(output)
    agent = Agent(
        system_prompt=SUMMARY_AGENT_PROMPT,
        model=get_pydanticai_openai_llm(),
        output_type=str,
    )

    summary = await agent.run(user_prompt=f"The user input is: {output_string}")
    return summary.output
