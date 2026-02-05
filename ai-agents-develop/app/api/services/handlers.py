import asyncio

import logfire


def make_action_execution_event_handler(remote_service):
    def handler(instance, event_type):
        if event_type in {"update"}:
            try:
                asyncio.create_task(remote_service.patch_action_execution(instance))
            except Exception as e:
                logfire.error(f"Failed to patch action execution", error=str(e))

    return handler


def make_control_execution_event_handler(remote_service):
    def handler(instance, event_type):
        if event_type in {"update"}:
            try:
                asyncio.create_task(remote_service.patch_control_execution(instance))
            except Exception as e:
                logfire.error(f"Failed to patch control execution", error=str(e))

    return handler
