import asyncio
import random
from typing import List
from uuid import UUID

import logfire
from alltrue.agents.schema.action_execution import LogContent, LogEntry

from app.core.models.models import ActionExecution, trigger_event
from app.core.storage_dependencies.storage_dependencies import get_provider


async def tool_call_log(
    action_id: UUID, log_content: List[LogContent], max_retries: int = 3
):
    """
    Add a log entry to an ActionExecution using atomic append to prevent lost updates.

    This function uses the repository's append_json_field method to atomically
    append log entries without the read-modify-write race condition.

    Args:
        action_id: UUID of the ActionExecution to update
        log_content: Log content to add
        max_retries: Maximum number of retry attempts for concurrent update conflicts
    """
    for attempt in range(max_retries + 1):
        try:
            async with get_provider() as async_provider:
                db = async_provider.get_repository(ActionExecution)

                # Create the log entry
                log_entry = LogEntry(content=log_content)
                log_data = log_entry.model_dump()

                # Use the repository's atomic append method
                success = await db.append_json_field(action_id, "log", log_data)
                if not success:
                    logfire.error(
                        f"Failed to append log to ActionExecution {action_id}"
                    )
                    raise ValueError(
                        f"Failed to append log to ActionExecution {action_id} - possible concurrent modification"
                    )
                else:
                    action_exec = await db.get(action_id)
                    trigger_event(action_exec, "update")
                    return

        except Exception as e:
            # Check if this is likely a race condition (concurrent modification)
            error_str = str(e).lower()
            is_race_condition = any(
                keyword in error_str
                for keyword in [
                    "concurrent",
                    "conflict",
                    "race",
                    "integrity",
                    "constraint",
                    "locked",
                    "timeout",
                    "deadlock",
                    "database is locked",
                ]
            )

            if attempt < max_retries and is_race_condition:
                # Calculate exponential backoff delay with jitter
                base_delay = 0.1 * (2**attempt)
                jitter = random.uniform(0, 0.05)  # Add some randomness
                delay = base_delay + jitter

                logfire.warning(
                    f"Race condition detected for action_id {action_id} (attempt {attempt + 1}), "
                    f"retrying in {delay:.3f}s. Error: {str(e)}"
                )
                await asyncio.sleep(delay)
            elif attempt < max_retries:
                # Non-race condition error, but still retry
                delay = 0.1 * (2**attempt)
                logfire.warning(
                    f"Update attempt {attempt + 1} failed for action_id {action_id}, "
                    f"retrying in {delay}s. Error: {str(e)}"
                )
                await asyncio.sleep(delay)
            else:
                # Final attempt failed
                logfire.error(
                    f"Failed to update ActionExecution {action_id} after {max_retries + 1} attempts. "
                    f"Final error: {str(e)}"
                )
                raise


async def tool_call_log_safe(action_id: UUID, log_content: List[LogContent]):
    """
    Safe version of tool_call_log that catches and logs all exceptions.

    This version will never raise exceptions, making it safe to use in
    contexts where you don't want log failures to crash the application.

    Args:
        action_id: UUID of the ActionExecution to update
        log_content: Log content to add
    """
    try:
        await tool_call_log(action_id, log_content)
    except Exception as e:
        logfire.error(
            f"Failed to add log to ActionExecution {action_id}: {str(e)}. "
            f"Log content was: {log_content}"
        )
