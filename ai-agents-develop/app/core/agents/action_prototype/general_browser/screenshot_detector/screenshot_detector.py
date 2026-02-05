#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.

from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class ScreenshotInfoResult(BaseModel):
    include_info: Literal["yes", "no"]
    reason: str


# target_content: "in the label section, thereis no pri"
async def filter_relevant_screenshots(
    page_content: str, target_information: str, screenshot: bytes
) -> Literal["yes", "no"]:
    agent_system_prompt = f"""
        You are an AI agent. Your job is to read the HTML source and the screenshot of a web page and determine if a specific piece of information appears anywhere in the page.

        If the information is present, set the `include_info` flag to "yes" and return it.

        If not, set the `include_info` flag to "no" and return it.

        Do not explain or provide any other output for `include_info` field, just "yes" or "no".

        But you also need to provide a reason for your decision in the `reason` field why you think the information is present or not.
        """
    agent = Agent(
        model=get_pydanticai_openai_llm(),
        system_prompt=agent_system_prompt,
        output_type=ScreenshotInfoResult,
    )
    user_prompt = [f" \n HTML Source is: \n{{{page_content}}}"]
    user_prompt.append(BinaryContent(data=screenshot, media_type="image/png"))
    user_prompt.append(
        f" \n Information you need to check is: \n{{{target_information}}}"
    )
    result = await agent.run(user_prompt)
    output = ScreenshotInfoResult.model_validate(result.output)
    return output.include_info
