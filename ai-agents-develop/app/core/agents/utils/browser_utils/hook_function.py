from typing import List

import logfire
from alltrue.agents.schema.action_execution import (
    LogContent,
    ObjectLog,
    PlainTextLog,
    S3ScreenshotLog,
)
from browser_use import Agent as BrowserUseAgent

from app.core.agents.utils.browser_utils.screenshot_upload import (
    S3ScreenshotUploadResult,
    upload_screenshot,
)


def generate_model_output_logs(agent: BrowserUseAgent) -> List[LogContent]:
    logs: List[LogContent] = []
    model_output = agent.state.last_model_output
    if model_output:
        logfire.info(model_output.thinking)
        logfire.info(model_output.evaluation_previous_goal)
        logfire.info(model_output.memory)
        logfire.info(model_output.next_goal)
        logs.append(
            ObjectLog(
                data={
                    "thinking": model_output.thinking,
                    "evaluation_previous_goal": model_output.evaluation_previous_goal,
                    "memory": model_output.memory,
                    "next_goal": model_output.next_goal,
                }
            )
        )
    return logs


def generate_screenshot_logs(agent: BrowserUseAgent) -> List[LogContent]:
    logs: List[LogContent] = []
    try:
        screenshots = agent.history.screenshots()
        screenshot_b64 = screenshots[-1] if screenshots else None
        if screenshot_b64:
            upload_result = upload_screenshot(screenshot_b64, context={})
            if isinstance(upload_result, S3ScreenshotUploadResult):
                logs.append(
                    S3ScreenshotLog(
                        key=upload_result.key, bucket=upload_result.bucket_name
                    )
                )
            else:
                logs.append(PlainTextLog(data=f"Screenshot: {upload_result.file_path}"))
    except Exception as e:
        logfire.error(f"Error in uploading screenshot: {e}")
        raise
    return logs
