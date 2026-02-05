from uuid import UUID

import logfire
from alltrue.agents.schema.control_execution import (
    GetControlExecutionStatusResponse,
    PostControlExecutionRequest,
    PostControlExecutionResponse,
)
from alltrue.queue.task import QueuedBackgroundTasks
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies.queue_manager import get_background_tasks
from app.api.services.control_execution_service import (
    ResetControlExecutionHeadToIndexRequest,
    ResetControlExecutionHeadToIndexResponse,
    ResumeControlExecutionRequest,
    ResumeControlExecutionResponse,
    RunControlExecutionRequest,
    RunControlExecutionResponse,
)
from app.api.services.control_execution_service import (
    create_control_only as service_create_control_only,
)
from app.api.services.control_execution_service import (
    execute_control as service_execute_control,
)
from app.api.services.control_execution_service import (
    get_control_execution as service_get_control_execution,
)
from app.api.services.control_execution_service import (
    reset_control_execution_head_to_index as service_reset_control_execution_head_to_index,
)
from app.api.services.control_execution_service import (
    resume_control_execution as service_resume_control_execution,
)
from app.api.services.control_execution_service import (
    run_control_only as service_run_control_only,
)
from app.core.storage_dependencies.repositories.providers import RepositoryProvider
from app.core.storage_dependencies.storage_dependencies import get_provider_dependency
from app.exceptions.control_exceptions import ControlExecutionNotFoundException

router = APIRouter(tags=["control_execution"])


@router.post(
    "/control-executions",
    status_code=200,
    description="Execute a control",
    response_model=PostControlExecutionResponse,
)
async def execute_control_endpoint(
    request: PostControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks = Depends(
        get_background_tasks
    ),
):
    try:
        control_execution, action_executions = await service_execute_control(
            exec_request=request,
            background_tasks=background_tasks,
        )
        return PostControlExecutionResponse(
            control_execution=control_execution,
            action_executions=action_executions,
        )
    except Exception as e:  # pragma: no cover
        logfire.exception("Error executing control", exception=e)
        raise HTTPException(status_code=500, detail=f"Error executing control: {e}")


@router.post(
    "/control-execution/create-only",
    status_code=200,
    description="Create or update a control execution without running",
    response_model=PostControlExecutionResponse,
)
async def create_control_only_endpoint(
    request: PostControlExecutionRequest,
):
    try:
        control_execution, action_executions = await service_create_control_only(
            exec_request=request,
        )
        return PostControlExecutionResponse(
            control_execution=control_execution,
            action_executions=action_executions,
        )
    except Exception as e:  # pragma: no cover
        logfire.exception("Error creating control execution only", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error creating control execution only: {e}"
        )


@router.post(
    "/control-execution/run",
    status_code=200,
    description="Run an existing control execution with optional step-by-step mode",
    response_model=RunControlExecutionResponse,
)
async def run_control_only_endpoint(
    request: RunControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks = Depends(
        get_background_tasks
    ),
):
    try:
        result = await service_run_control_only(
            request=request, background_tasks=background_tasks
        )
        return result
    except Exception as e:  # pragma: no cover
        logfire.exception("Error running control execution", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error running control execution: {e}"
        )


@router.post(
    "/control-execution/reset-head-to-index",
    status_code=200,
    description="Reset the head of a control execution to a specific index",
    response_model=ResetControlExecutionHeadToIndexResponse,
)
async def reset_control_execution_head_to_index_endpoint(
    request: ResetControlExecutionHeadToIndexRequest,
):
    try:
        result = await service_reset_control_execution_head_to_index(
            request=request,
        )
        return result
    except ControlExecutionNotFoundException as e:
        logfire.exception("ControlExecution not found", exception=e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:  # pragma: no cover
        logfire.exception(
            "Error resetting control execution head to index", exception=e
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting control execution head to index: {e}",
        )


@router.post(
    "/control-execution/resume",
    status_code=200,
    description="Resume a control execution with extra instructions and optional step-by-step mode",
    response_model=ResumeControlExecutionResponse,
)
async def resume_control_execution_endpoint(
    request: ResumeControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks = Depends(
        get_background_tasks
    ),
):
    try:
        result = await service_resume_control_execution(
            request=request, background_tasks=background_tasks
        )
        return result
    except Exception as e:  # pragma: no cover
        logfire.exception("Error resuming control execution", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error resuming control execution: {e}"
        )


@router.get(
    "/control-executions/{control_execution_id}",
    status_code=200,
    response_model=GetControlExecutionStatusResponse,
    description="Get the status of a control execution",
)
async def get_control_execution_endpoint(
    control_execution_id: UUID,
    provider: RepositoryProvider = Depends(get_provider_dependency),
):
    try:
        res = await service_get_control_execution(control_execution_id, provider)
        return res
    except ControlExecutionNotFoundException:  # pragma: no cover
        logfire.exception(
            "ControlExecution not found", control_execution_id=control_execution_id
        )
        raise HTTPException(
            status_code=404,
            detail=f"ControlExecution with id {control_execution_id} not found",
        )
    except Exception as e:  # pragma: no cover
        logfire.exception("Error retrieving control execution", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving control execution: {e}"
        )
