import base64

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class FeedbackInfo(BaseModel):
    new_feedback: str


# target_content: "in the label section, thereis no pri"
async def get_real_feedback(
    original_feedback: str, screenshot: str, user_prompt: str
) -> str:
    agent_system_prompt = f"""
        You are responsible for writing feedback to a user to help them improve their instructions to an AI Agent that got stuck during its task. You will be given:

        The instructions the user provided to the agent,
        A screenshot showing where the agent got stuck,
        A failure reason describing what the agent failed to do.

        Your job is to write clear and actionable feedback to the user explaining how their instructions can be improved to help the agent succeed.

        In particular, if the agent missed a UI element that is visible or accessible via scrolling, searching, clicking an expansion panel or similar, you should suggest that the user update their instructions to explicitly mention this action to locate the desired item.

        Use the screenshot to analyze what UI elements are visible or hidden, and what the agent might have overlooked. Your feedback should help the user write more robust instructions that guide the agent through such situations.
        """
    agent = Agent(
        model=get_pydanticai_openai_llm(),
        system_prompt=agent_system_prompt,
        output_type=FeedbackInfo,
    )
    if screenshot:
        try:
            image_bytes = base64.b64decode(screenshot)
        except Exception as e:
            logfire.warning(f"Error decoding screenshot")
            image_bytes = None

    if image_bytes:
        input_prompt = [
            f"The original feedback is: \n {original_feedback}. \n And the original user prompt input is: \n {user_prompt} \n The screenshot of the failed webpage is as follows: \n"
        ]
        input_prompt.append(BinaryContent(data=image_bytes, media_type="image/png"))
    else:
        input_prompt = [
            f"The original feedback is: \n {original_feedback}. \n And the original user prompt input is: \n {user_prompt}"
        ]

    result = await agent.run(input_prompt)
    return FeedbackInfo.model_validate(result.output).new_feedback
