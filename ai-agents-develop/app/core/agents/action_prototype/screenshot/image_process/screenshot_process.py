import base64
import binascii
from datetime import datetime
from typing import List, Literal

from browser_use.browser import BrowserSession
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class ImageSelectionResult(BaseModel):
    selected_image_index: List[int]
    include_all_info: Literal["yes", "no"]
    info_not_found: List[str]


async def take_screenshot(
    browser_session: BrowserSession,
    full_page: bool = False,
) -> bytes:
    screenshot_b64 = await browser_session.take_screenshot(full_page=full_page)
    try:
        return base64.b64decode(screenshot_b64)
    except binascii.Error as exc:
        raise ValueError("Browser returned invalid base64 screenshot") from exc


# target_content: "in the label section, thereis no pri"
async def filter_relevant_screenshots(
    screenshots: list[bytes], info_content: str
) -> ImageSelectionResult:
    agent_system_prompt = f"""
        Your task is to analyze a list of screenshots and determine if the complete information content is found across them.

        You must return:
        1. The *smallest set* of image indexes (from 0 to N-1) that together contain the complete information content.
        2. Whether this set *includes all the required Information content*.
        3. A list of any specific items or points of Information content that were *not found*.

        Rules:
        - The images may contain duplicate or partially overlapping content.
        - Do NOT include unnecessary images; only select the minimum required images that *together* fulfill the request.
        - You must correlate Information content *across multiple images* if necessary (e.g., "event A happened before event B" when A is in image 0 and B in image 1).
        - Be cautious not to miss relevant images just because the Information content is split.
        - Do **not** exclude an image just because it does not contain all content — select it if it contributes any unique, needed part.
        - The image list is zero-indexed. If there are 3 images, valid indexes are: 0, 1, 2. Never use a number ≥ {len(screenshots)}.
        - If any required Information content is missing or unclear, set `include_all_info = "no"` and explain which part(s) in `info_not_found`.

        Additional constraints:
        - Some images may include relative dates (e.g., "last week"); estimate them based on today's date: {datetime.now().strftime('%Y-%m-%d')}.
        - You do not need to be precise about missing timestamps.
        - Ensure the *order of comments* or *events* respects the actual chronological or logical sequence shown.
        - If any numbers are shown, treat them *literally* — do not assume, infer, or "fill in" values not explicitly visible.
        """
    agent = Agent(
        model=get_pydanticai_openai_llm(),
        system_prompt=agent_system_prompt,
        output_type=ImageSelectionResult,
    )
    user_prompt = [
        f"The Information content is: {info_content}. \n and the images are: "
    ]
    for screenshot in screenshots:
        user_prompt.append(BinaryContent(data=screenshot, media_type="image/png"))
    user_prompt.append(
        f" \n You must check each image and return the indexes of the images that contain all or parts of the information content."
    )

    result = await agent.run(user_prompt)
    return ImageSelectionResult.model_validate(result.output)
