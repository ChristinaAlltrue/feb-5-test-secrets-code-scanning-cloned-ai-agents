from pydantic import BaseModel
from pydantic_ai import Agent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class FailedLogException(Exception):
    """Custom exception raised for errors in the file tool."""


class FailedLog(BaseModel):
    explanation: str


async def failed_log_generator(info_content: str) -> str:
    try:
        agent_system_prompt = f"""
            Your task is to analyze a feedback from the browser navigation and return an explanation of the failed navigation.
            You need to tell the user what went wrong and what they can do to fix it.
            """
        agent = Agent(
            model=get_pydanticai_openai_llm(),
            system_prompt=agent_system_prompt,
            output_type=FailedLog,
        )
        user_prompt = f" \n The information content is: {info_content}."
        result = await agent.run(user_prompt)
        output = FailedLog.model_validate(result.output)
        return output.explanation
    except Exception as e:
        raise FailedLogException(
            f"Failed to generate failed log explanation: {str(e)}"
        ) from e
