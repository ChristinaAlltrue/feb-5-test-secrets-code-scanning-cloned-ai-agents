import os
import threading

import logfire
from logfire import ConsoleOptions

from app.api.services.handlers import (
    make_action_execution_event_handler,
    make_control_execution_event_handler,
)
from app.api.services.remote_update_service import ControlPlaneUpdateService
from app.core.models.models import ActionExecution, ControlExecution
from app.core.registry import ensure_registry_loaded
from app.utils.file_storage_manager import get_file_storage
from config import AGENTS_EVIDENCE_STORAGE_BUCKET, CONTROL_PLANE_EVENT_HANDLER_ENABLED

_WORKER_INITIALIZED_LOCK = threading.Lock()
_WORKER_INITIALIZED = False


def initialize_worker_dependencies():
    """
    The worker is different from the api service process, we need to initialize the registry in the worker process.
    """
    global _WORKER_INITIALIZED

    with _WORKER_INITIALIZED_LOCK:
        logfire.info(f"Checking worker initialized: {_WORKER_INITIALIZED}")
        if _WORKER_INITIALIZED:
            return
        logfire.info("Initializing worker dependencies")
        # Configure registry
        logfire.info("Initializing registry")
        ensure_registry_loaded()
        # Configure control plane event handler
        if CONTROL_PLANE_EVENT_HANDLER_ENABLED:
            logfire.info("Initializing control plane event handler")
            control_plane_update_service = ControlPlaneUpdateService()
            ActionExecution.register_event_handler(
                make_action_execution_event_handler(control_plane_update_service)
            )
            ControlExecution.register_event_handler(
                make_control_execution_event_handler(control_plane_update_service)
            )
        # Configure file storage
        logfire.info(f"Initializing file storage: {AGENTS_EVIDENCE_STORAGE_BUCKET}")
        get_file_storage(AGENTS_EVIDENCE_STORAGE_BUCKET)

        # Configure logfire
        logfire.configure(
            send_to_logfire="if-token-present",
            scrubbing=False,
            console=ConsoleOptions() if os.getenv("LOCAL_ACCESS") else None,
        )
        logfire.instrument_requests(
            excluded_urls="https://search-*"  # exclude opensearch requests from tracing
        )
        logfire.instrument_httpx(
            excluded_urls="https://search-*"  # exclude opensearch requests from tracing
        )
        logfire.instrument_pydantic_ai()
        _WORKER_INITIALIZED = True
