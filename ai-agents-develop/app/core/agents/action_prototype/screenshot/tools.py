from pathlib import Path
from uuid import uuid4

import logfire
from alltrue.local.file_storage.cloud_file_storage import CloudFileStorage
from browser_use.browser import BrowserSession
from pydantic_ai import RunContext

from app.core.agents.action_prototype.screenshot.image_process.image_spliter import (
    split_image_by_spacing,
)
from app.core.agents.action_prototype.screenshot.image_process.screenshot_process import (
    ImageSelectionResult,
    filter_relevant_screenshots,
    take_screenshot,
)
from app.core.agents.action_prototype.screenshot.schema import (
    LocalScreenshotUploadResult,
    S3ScreenshotUploadResult,
    ScreenshotOutput,
    ScreenshotUploadResult,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.utils.file_storage_manager import get_file_storage


class ProcessingScreenshotException(Exception):
    """Custom exception raised for errors in processing screenshots."""


MAX_FIRST_FILTER_RETRIES = 3
MAX_SECOND_FILTER_RETRIES = 2


def _should_retry_filtering(
    filtered_screenshots: ImageSelectionResult, lists_of_screenshots: list[bytes]
) -> bool:
    ret = (
        len(filtered_screenshots.selected_image_index) == 0
        or len(filtered_screenshots.selected_image_index) == len(lists_of_screenshots)
        or (filtered_screenshots.include_all_info == "no")
    )
    return ret


async def _retry_filter_screenshots(
    screenshots: list[bytes],
    target_info: str,
    max_retries: int,
) -> ImageSelectionResult:
    """Helper function to handle retry logic for screenshot filtering."""
    filtered_screenshots = await filter_relevant_screenshots(screenshots, target_info)
    try_times = max_retries
    logfire.info(f"Starting screenshot filtering with {try_times} retry attempts")
    # check again if the filtered screenshots:
    # 1. not include all required information
    # 2. selected_image_index is empty
    # 3. It contains all original images
    while _should_retry_filtering(filtered_screenshots, screenshots) and try_times > 0:
        # If not all info is included, we need to re filter the screenshots
        logfire.info(
            f"Retry {max_retries+1-try_times}: Information incomplete in filtered screenshots"
        )
        filtered_screenshots = await filter_relevant_screenshots(
            screenshots, target_info
        )
        try_times -= 1
    return filtered_screenshots


async def screenshot_action(
    browser_session: BrowserSession, full_page_screenshot: bool, target_info: str
) -> list[bytes]:
    screenshots = []
    screenshot = await take_screenshot(browser_session, full_page_screenshot)
    # Old code for splitting images:
    lists_of_screenshots = split_image_by_spacing(input_image=screenshot)
    filtered_screenshots = await _retry_filter_screenshots(
        lists_of_screenshots, target_info, MAX_FIRST_FILTER_RETRIES
    )
    # If we still don't have all the info after retries, we will log a warning
    if _should_retry_filtering(filtered_screenshots, lists_of_screenshots):
        logfire.info(
            f"Could not include all required information after retries in the first filtering"
        )
        screenshots.append(screenshot)
    else:
        tmp_screenshots = [
            lists_of_screenshots[i] for i in filtered_screenshots.selected_image_index
        ]
        # run the filter again to remove the extra screenshots as soon as possible
        filtered_screenshots = await _retry_filter_screenshots(
            lists_of_screenshots, target_info, MAX_SECOND_FILTER_RETRIES
        )
        # If its `include_all_info` is True after the filtering,
        # we will return the selected images
        # Otherwise, we will log a warning and return the original screenshots
        if filtered_screenshots.include_all_info:
            screenshots = [
                tmp_screenshots[i] for i in filtered_screenshots.selected_image_index
            ]
        else:
            logfire.warning(
                f"Could not include all required information after retries in the second filtering"
            )
            screenshots = tmp_screenshots
    return screenshots


async def process_screenshot_info(
    url: str,
    browser_session: BrowserSession,
    target_info: str,
) -> list[bytes]:
    """
    Process target_info by locating target elements and taking screenshots.
    """
    page = await browser_session.get_current_page()
    try:
        await page.goto(url)
        await page.evaluate("window.scrollTo(0, 0);")
        full_page_screenshot = True
        screenshots = await screenshot_action(
            browser_session, full_page_screenshot, target_info
        )
        return screenshots
    except Exception as e:
        logfire.error(
            f"Error processing screenshot for browser context with URL: {url}: raising {e}"
        )
        raise ProcessingScreenshotException(f"Error when process screenshots: {e}")
    finally:
        await page.close()


async def start_screen_agent(
    ctx: RunContext[ActionDeps], target_url: str, target_information: str
) -> ScreenshotOutput:
    browser_deps = ctx.deps.get_browser_deps()
    if not browser_deps:
        ctx.deps.init_browser_deps()
        browser_deps = ctx.deps.get_browser_deps()
    browser_session = browser_deps.browser_session
    screenshots = await process_screenshot_info(
        target_url,
        browser_session,
        target_information,
    )
    # TODO: save screenshots part
    img_list = []
    for screenshot in screenshots:
        img_list.append(upload_screenshot(screenshot, {}))
    result = ScreenshotOutput(
        img_list=img_list,
        target_url=target_url,
    )
    return result


# TODO: this will be removed when iter 4 is done
def upload_screenshot(screenshot_bytes: bytes, context: dict) -> ScreenshotUploadResult:
    """
    Upload a base64-encoded screenshot to file storage and return an access path.
    Args:
        screenshot_b64: Base64-encoded PNG screenshot data
        context: Context dictionary passed to storage methods
    Returns:
        ScreenshotUploadResult containing storage-specific metadata
        (S3: key and bucket info, Local: file name and path)
    """
    file_storage = get_file_storage()
    file_name = f"screenshot_{uuid4()}.png"
    file_storage.upload_object(
        context=context,
        object_bytes=screenshot_bytes,
        object_name=file_name,
    )
    if isinstance(file_storage, CloudFileStorage):
        return S3ScreenshotUploadResult(key=file_name, bucket_name=file_storage.bucket)
    else:
        return LocalScreenshotUploadResult(
            file_name=file_name,
            file_path=str(Path(file_storage.local_storage_dir) / file_name),
        )
