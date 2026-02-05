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

from contextlib import AsyncExitStack, asynccontextmanager

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    action_execution,
    action_prototype,
    command_interpreter,
    control_execution,
    framework,
    health,
)
from app.api.routes import llm_models as models_router
from app.api.routes import tools as tools_router
from app.api.services.handlers import (
    make_action_execution_event_handler,
    make_control_execution_event_handler,
)
from app.api.services.remote_update_service import ControlPlaneUpdateService

# Import prototype loader, initialize the prototype registry
from app.core import prototype_loader  # noqa: F401 # type: ignore
from app.core.models.models import ActionExecution, ControlExecution
from app.utils.file_storage_manager import close_file_storage, get_file_storage
from app.utils.queue import get_queue_manager, stop_queue_manager
from app.utils.scheduler.scheduler import initialize_scheduler, shutdown_scheduler
from config import (
    AGENTS_EVIDENCE_STORAGE_BUCKET,
    CONTROL_PLANE_EVENT_HANDLER_ENABLED,
    RQ_BACKGROUND_TASKS_ENABLED,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:

        async def async_stop(cb, *args, **kwargs):
            """
            Async callback wrapper for synchronous functions
            """
            cb(*args, **kwargs)

        if RQ_BACKGROUND_TASKS_ENABLED:
            QM = get_queue_manager()  # This will initialize it
            QM.start_workers()
            logfire.info("Application queue manager initialized successfully")
            stack.push_async_callback(async_stop, stop_queue_manager)
        else:
            logfire.warning("RQ disabled, skipping queue manager initialization")

        # Storage
        get_file_storage(AGENTS_EVIDENCE_STORAGE_BUCKET)  # This will initialize it
        stack.push_async_callback(async_stop, close_file_storage)
        logfire.info("Application storage initialized successfully")

        # Scheduler
        await initialize_scheduler()
        logfire.info("Application scheduler service initialized successfully")
        stack.push_async_callback(shutdown_scheduler)

        # Control plane event handler
        if CONTROL_PLANE_EVENT_HANDLER_ENABLED:
            control_plane_update_service = ControlPlaneUpdateService()
            ActionExecution.register_event_handler(
                make_action_execution_event_handler(control_plane_update_service)
            )
            ControlExecution.register_event_handler(
                make_control_execution_event_handler(control_plane_update_service)
            )

        yield


ROOT_PATH = "/v1/ai-agents"
app: FastAPI = FastAPI(title="AI Agents API", root_path=ROOT_PATH, lifespan=lifespan)

# TODO: restrict origins, currently all origins are allowed for development
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logfire.instrument(app)

# Include all routers
app.include_router(health.router)
app.include_router(action_prototype.router)
app.include_router(control_execution.router)
app.include_router(action_execution.router)
app.include_router(framework.router)
app.include_router(command_interpreter.router)
app.include_router(tools_router.router)
app.include_router(models_router.router)
