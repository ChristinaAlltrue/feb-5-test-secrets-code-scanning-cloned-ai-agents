import re
from typing import Any

import logfire
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

# Warning prefix used by detect_tool_call_loop_processor
TOOL_LOOP_WARNING_PREFIX = "⚠️ WARNING: Loop detected!"


@logfire.instrument("limit_browser_tool_call_history_processor")
async def limit_browser_tool_call_history_processor(
    messages: list[ModelMessage], max_tool_calls: int = 8
) -> list[ModelMessage]:
    """Limit the browser tool call history to the last N calls (only tools with 'browser_' prefix)"""
    logfire.info(f"Limiting browser tool call history to last {max_tool_calls} calls")
    logfire.info(f"Input: {len(messages)} total messages")

    # Count browser tool calls and find their indices
    browser_tool_call_indices: list[int] = []
    for i, msg in enumerate(messages):
        if msg.kind == "response" and isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart) and part.tool_name.startswith(
                    "browser_"
                ):
                    browser_tool_call_indices.append(i)
                    logfire.info(
                        f"Found browser tool call at index {i}: {part.tool_name}"
                    )
                    break

    browser_tool_call_count = len(browser_tool_call_indices)
    logfire.info(f"Total browser tool calls found: {browser_tool_call_count}")

    # Limit to last N browser tool calls if needed
    if browser_tool_call_count > max_tool_calls:
        # Keep only the last N browser tool calls, remove the older ones
        # Each tool call is a pair: ModelResponse (with ToolCallPart) + ModelRequest (with ToolReturnPart)
        old_browser_tool_call_indices = browser_tool_call_indices[:-max_tool_calls]
        logfire.info(
            f"Removing {len(old_browser_tool_call_indices)} old browser tool calls at indices: {old_browser_tool_call_indices}"
        )

        # Create set of indices to remove (tool call response + the following tool return request)
        indices_to_remove: set[int] = set()
        for idx in old_browser_tool_call_indices:
            indices_to_remove.add(idx)  # The tool call response
            if idx + 1 < len(messages):
                indices_to_remove.add(idx + 1)  # The tool return request

        # Also remove warning messages that may have been added after removed browser tool calls
        # Find the highest index of removed browser tool calls to determine the cutoff
        if old_browser_tool_call_indices:
            highest_removed_idx = max(
                idx + 1 if idx + 1 < len(messages) else idx
                for idx in old_browser_tool_call_indices
            )

            # Look for warning messages that appear after or near removed tool calls
            for i, msg in enumerate(messages):
                if (
                    i not in indices_to_remove
                    and msg.kind == "request"
                    and isinstance(msg, ModelRequest)
                ):
                    for part in msg.parts:
                        if isinstance(part, UserPromptPart) and part.content.startswith(
                            TOOL_LOOP_WARNING_PREFIX
                        ):
                            # If this warning appears anywhere from the start up to shortly after
                            # the highest removed index, it might be related to removed tool calls
                            # Remove it if it's before or around the kept tool calls start
                            if (
                                i <= highest_removed_idx + 5
                            ):  # Small buffer for related messages
                                indices_to_remove.add(i)
                                logfire.info(
                                    f"Removing warning message at index {i} that may be associated with removed browser tool calls"
                                )
                            break

        logfire.info(f"Total message indices to remove: {sorted(indices_to_remove)}")

        # Filter out the old browser tool calls and associated warnings
        filtered_messages: list[ModelMessage] = []
        for i, msg in enumerate(messages):
            if i not in indices_to_remove:
                filtered_messages.append(msg)

        messages = filtered_messages
        logfire.info(
            f"After filtering: {len(messages)} messages remaining (removed {len(indices_to_remove)} messages)"
        )
    else:
        logfire.info(
            f"Browser tool call count ({browser_tool_call_count}) is within limit, no filtering needed"
        )

    logfire.info(f"Output: {len(messages)} total messages")
    return messages


@logfire.instrument("trim_page_snapshots_processor")
async def trim_page_snapshots_processor(
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    """Trim all page snapshots except the last one to save context"""
    logfire.info("Trimming page snapshots to keep only the last one")
    logfire.info(f"Input: {len(messages)} total messages")

    def has_snapshot(content: str) -> bool:
        """Check if content contains a Page Snapshot"""
        if type(content) != str:
            # TODO: sometimes it return a list and then raise error, will handle properly later when we figure out what is the content
            return False
        return bool(re.search(r"- Page Snapshot[:\s]*\n```yaml\n", content))

    def trim_snapshot_from_content(content: str) -> str:
        """Trim the Page Snapshot section from tool return content"""
        # Pattern to match "- Page Snapshot" or "- Page Snapshot:" followed by yaml block
        pattern = r"(- Page Snapshot[:\s]*\n```yaml\n.*?\n```)"
        trimmed = re.sub(
            pattern,
            "- Page Snapshot: [Omitted to save context]",
            content,
            flags=re.DOTALL,
        )
        return trimmed

    # First pass: find all messages with snapshots
    snapshot_message_indices: list[int] = []
    for i, msg in enumerate(messages):
        if msg.kind == "request" and isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart) and has_snapshot(part.content):
                    snapshot_message_indices.append(i)
                    logfire.info(
                        f"Found snapshot at index {i} from tool: {part.tool_name}"
                    )
                    break

    logfire.info(f"Total snapshots found: {len(snapshot_message_indices)}")

    if len(snapshot_message_indices) > 1:
        logfire.info(
            f"Keeping only the last snapshot, will trim {len(snapshot_message_indices) - 1} earlier snapshots"
        )

        # Keep the last snapshot index
        last_snapshot_index = snapshot_message_indices[-1]
        indices_to_trim = set(snapshot_message_indices[:-1])
        logfire.info(
            f"Last snapshot at index {last_snapshot_index}, trimming indices: {sorted(indices_to_trim)}"
        )

        # Second pass: trim snapshots from all but the last
        processed_messages: list[ModelMessage] = []
        trimmed_count = 0

        for i, msg in enumerate(messages):
            if (
                i in indices_to_trim
                and msg.kind == "request"
                and isinstance(msg, ModelRequest)
            ):
                # Trim snapshots from this message
                new_parts = []
                for part in msg.parts:
                    if isinstance(part, ToolReturnPart) and has_snapshot(part.content):
                        trimmed_content = trim_snapshot_from_content(part.content)
                        new_parts.append(
                            ToolReturnPart(
                                tool_name=part.tool_name,
                                content=trimmed_content,
                                tool_call_id=part.tool_call_id,
                            )
                        )
                        logfire.info(
                            f"Trimmed snapshot from {part.tool_name} at index {i}"
                        )
                        trimmed_count += 1
                    else:
                        new_parts.append(part)
                processed_messages.append(ModelRequest(parts=new_parts))
            else:
                processed_messages.append(msg)

        logfire.info(f"Snapshot trimming complete: kept 1, trimmed {trimmed_count}")
        messages = processed_messages
    elif len(snapshot_message_indices) == 1:
        logfire.info("Only 1 snapshot found, no trimming needed")
    else:
        logfire.info("No snapshots found")

    logfire.info(f"Output: {len(messages)} total messages")
    return messages


@logfire.instrument("detect_tool_call_loop_processor")
async def detect_tool_call_loop_processor(
    messages: list[ModelMessage],
    consecutive_limit: int = 3,
) -> list[ModelMessage]:
    """
    Detect when the LLM calls the same tool(s) with the same arguments consecutively.
    After N consecutive identical calls (default 3), inject a warning user message.

    Handles both single tool calls and groups of tool calls in a single response.
    If a response contains multiple tools, they are treated as a group, and the
    entire group must repeat to be considered a loop.

    Example:
    - Single tool: tool_A -> tool_A -> tool_A -> warning
    - Tool group: [tool_A, tool_B] -> [tool_A, tool_B] -> [tool_A, tool_B] -> warning

    Args:
        messages: List of conversation messages
        consecutive_limit: Number of consecutive identical calls/groups before warning (default 3)

    Returns:
        Modified message list with warning injected if loop detected
    """
    logfire.info(
        f"Checking for tool call loops (consecutive limit: {consecutive_limit})"
    )
    logfire.info(f"Input: {len(messages)} total messages")

    def serialize_tool_call(tool_name: str, tool_args: dict[str, Any]) -> str:
        """Create a comparable string representation of a tool call"""
        # Sort dict keys for consistent comparison
        sorted_args = {k: tool_args[k] for k in sorted(tool_args.keys())}
        return f"{tool_name}::{sorted_args}"

    def serialize_tool_group(tool_calls: list[tuple[str, dict[str, Any]]]) -> str:
        """Create a comparable string representation of a group of tool calls"""
        # Sort tool calls by serialized representation for consistent comparison
        serialized_calls = sorted(
            [serialize_tool_call(name, args) for name, args in tool_calls]
        )
        return "||".join(serialized_calls)

    # Track tool call groups per response message
    tool_call_groups: list[tuple[int, list[tuple[str, dict[str, Any]]], str]] = (
        []
    )  # (message_index, [(tool_name, args), ...], serialized_group)

    for i, msg in enumerate(messages):
        if msg.kind == "response" and isinstance(msg, ModelResponse):
            # Collect all tool calls in this response
            response_tool_calls: list[tuple[str, dict[str, Any]]] = []

            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_name = part.tool_name
                    # Handle different types of args - ensure we have a dict
                    if hasattr(part, "args"):
                        args = part.args
                        if isinstance(args, dict):
                            tool_args = args
                        elif hasattr(args, "model_dump"):  # Pydantic model
                            tool_args = args.model_dump()
                        elif isinstance(args, str):
                            tool_args = {"args": args}
                        else:
                            tool_args = {}
                    else:
                        tool_args = {}

                    response_tool_calls.append((tool_name, tool_args))
                    logfire.info(
                        f"Found tool call at index {i}: {tool_name} with args: {tool_args}"
                    )

            # If this response has tool calls, add it as a group
            if response_tool_calls:
                serialized_group = serialize_tool_group(response_tool_calls)
                tool_call_groups.append((i, response_tool_calls, serialized_group))
                logfire.info(
                    f"Response at index {i} has {len(response_tool_calls)} tool call(s): {[t[0] for t in response_tool_calls]}"
                )

    # Check for consecutive identical groups
    if len(tool_call_groups) >= consecutive_limit:
        # Look at the last N groups to see if they're identical
        last_n_groups = tool_call_groups[-consecutive_limit:]
        last_group_serialized = last_n_groups[0][2]

        # Check if all last N groups are identical
        if all(group[2] == last_group_serialized for group in last_n_groups):
            first_group_tools = last_n_groups[0][1]
            loop_indices = [group[0] for group in last_n_groups]

            logfire.warning(
                f"LOOP DETECTED: Tool group called {consecutive_limit} times consecutively with same args at indices {loop_indices}"
            )
            logfire.warning(
                f"Tool group: {[(name, args) for name, args in first_group_tools]}"
            )

            # Format the warning message based on single vs multiple tools
            if len(first_group_tools) == 1:
                tool_name, tool_args = first_group_tools[0]
                warning_text = (
                    f"{TOOL_LOOP_WARNING_PREFIX} You have called the tool '{tool_name}' "
                    f"{consecutive_limit} consecutive times with identical arguments. "
                    f"This usually indicates an error. Please try a different approach "
                    f"or verify if the previous attempts succeeded before calling again.\n\n"
                    f"Repeated call arguments: {tool_args}"
                )
            else:
                tool_names = [name for name, _ in first_group_tools]
                warning_text = (
                    f"{TOOL_LOOP_WARNING_PREFIX} You have called the same group of tools "
                    f"{consecutive_limit} consecutive times with identical arguments: {tool_names}\n"
                    f"This usually indicates an error. Please try a different approach "
                    f"or verify if the previous attempts succeeded before calling again.\n\n"
                    f"Repeated tool calls:\n"
                )
                for tool_name, tool_args in first_group_tools:
                    warning_text += f"  - {tool_name}: {tool_args}\n"

            # Create a user message with the warning
            warning_message = ModelRequest(parts=[UserPromptPart(content=warning_text)])

            # Append the warning message at the end
            messages.append(warning_message)
            logfire.info(
                f"Appended loop warning user message after {consecutive_limit} consecutive identical groups"
            )
        else:
            logfire.info(
                f"Last {consecutive_limit} groups are not identical, no loop detected"
            )
    else:
        logfire.info(
            f"Not enough tool call groups ({len(tool_call_groups)}) to check for loops"
        )

    logfire.info(f"Output: {len(messages)} total messages")
    return messages


def format2simple_dict(messages: list[ModelMessage]) -> list[dict[str, str]]:
    formatted_parts = []
    for message in messages:
        try:
            # if message.kind == 'request':
            for part in message.parts:
                role = part.__class__.__name__.replace("PromptPart", "").replace(
                    "Part", ""
                )
                content = getattr(part, "content", None)
                if content:
                    formatted_parts.append({"role": role, "content": content})
        except Exception as e:
            logfire.warning(f"Failed to process message: {e}")
            continue
    return formatted_parts


def format_model_messages(messages: list[ModelMessage]) -> list[str]:
    """Format model messages into a single string for logging or display"""
    simple_dict = format2simple_dict(messages)
    return [f"{part['role']}: {part['content']}" for part in simple_dict]
