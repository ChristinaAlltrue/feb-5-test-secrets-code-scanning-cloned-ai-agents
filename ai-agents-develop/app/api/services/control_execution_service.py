from typing import Any, Dict, List
from uuid import UUID

import logfire
from alltrue.agents.schema.control_execution import (
    GetControlExecutionStatusResponse,
    ResetControlExecutionHeadToIndexRequest,
    ResetControlExecutionHeadToIndexResponse,
    ResumeControlExecutionRequest,
    ResumeControlExecutionResponse,
    RunControlExecutionRequest,
    RunControlExecutionResponse,
)
from alltrue.agents.schema.customer_credential import CredentialValue
from alltrue.queue.task import QueuedBackgroundTasks
from fastapi import BackgroundTasks
from pydantic import BaseModel

from app.core.graph.run.resume import resume_graph
from app.core.graph.run.run import run_graph
from app.core.graph.run.utils import get_nodes_from_strings
from app.core.graph.sql_state_persistence.persistence import SqlStatePersistence
from app.core.models.models import ActionExecution, ControlExecution
from app.core.storage_dependencies.repositories.providers import RepositoryProvider
from app.core.storage_dependencies.storage_dependencies import get_provider
from app.exceptions.control_exceptions import ControlExecutionNotFoundException
from app.utils.folder_operation import (
    construct_control_execution_folder,
    setup_control_execution_folder_for_rerun,
)
from app.utils.worker import initialize_worker_dependencies
from config import RQ_BACKGROUND_TASKS_ENABLED, SQLITE_DATABASE_SYNC_URL


class ExecutionEntity(BaseModel):
    entity_id: UUID
    entity_exec_args: dict


from alltrue.agents.schema.control_execution import PostControlExecutionRequest


async def upsert_control_execution(
    control_execution_request: PostControlExecutionRequest,
):
    async with get_provider() as provider:
        control_execution = await provider.get_repository(ControlExecution).get(
            control_execution_request.control_execution_id,
        )
        if control_execution:
            return await update_control_execution_with_actions(
                provider,
                control_execution_request,
                control_execution,
            )
        else:
            return await create_control_execution_with_actions(
                control_execution_request,
            )


async def update_control_execution_with_actions(
    repository_provider: RepositoryProvider,
    control_execution_request: PostControlExecutionRequest,
    control_execution: ControlExecution,
):
    control_execution_repository = repository_provider.get_repository(ControlExecution)
    control_execution.customer_id = control_execution_request.customer_id
    control_execution.control_id = control_execution_request.control_id
    control_execution.entity_id = control_execution_request.entity_id
    control_execution.compliance_instruction = (
        control_execution_request.compliance_instruction
    )
    control_execution.entity_exec_args = control_execution_request.entity_exec_args
    control_execution.edges = [i.model_dump() for i in control_execution_request.edges]

    await control_execution_repository.update(control_execution)

    action_repo = repository_provider.get_repository(ActionExecution)
    action_execs: List[ActionExecution] = []
    for action_instance in control_execution_request.action_instances:
        action_execution = await action_repo.get(id=action_instance.id)
        if not action_execution:
            raise ValueError(f"ActionExecution with id {action_instance.id} not found.")

        action_execution.order = action_instance.order
        action_execution.action_prototype_name = action_instance.action_prototype_name
        action_execution.control_variables = {
            k: v.model_dump() for k, v in action_instance.control_variables.items()
        }
        action_execution.reference_variables = {
            k: v.model_dump() for k, v in action_instance.reference_variables.items()
        }
        action_execution.independent_variables = {
            k: v.model_dump() for k, v in action_instance.independent_variables.items()
        }
        action_execution.subagents = [
            subagent.model_dump(mode="json") for subagent in action_instance.subagents
        ]
        action_execution.control_execution_id = control_execution.id

        updated_action_execution = await action_repo.update(action_execution)
        action_execs.append(updated_action_execution)

    control_execution.action_execution_ids = [
        str(action_exec.id) for action_exec in action_execs
    ]
    await control_execution_repository.update(control_execution)

    return control_execution, action_execs


async def create_control_execution_with_actions(
    exec_request: PostControlExecutionRequest,
) -> tuple[ControlExecution, List[ActionExecution]]:
    control_execution = ControlExecution(
        id=exec_request.control_execution_id,
        customer_id=exec_request.customer_id,
        control_id=exec_request.control_id,
        entity_id=exec_request.entity_id,
        compliance_instruction=exec_request.compliance_instruction,
        entity_exec_args=exec_request.entity_exec_args,
        edges=[i.model_dump() for i in exec_request.edges],
    )
    async with get_provider() as provider:
        await provider.get_repository(ControlExecution).create(control_execution)
        action_execs = []
        for instance in exec_request.action_instances:
            action_exec = ActionExecution(
                id=instance.id,
                order=instance.order,
                action_prototype_name=instance.action_prototype_name,
                control_variables={
                    k: v.model_dump() for k, v in instance.control_variables.items()
                },
                reference_variables={
                    k: v.model_dump() for k, v in instance.reference_variables.items()
                },
                independent_variables={
                    k: v.model_dump() for k, v in instance.independent_variables.items()
                },
                subagents=[
                    subagent.model_dump(mode="json") for subagent in instance.subagents
                ],
                control_execution_id=control_execution.id,
            )
            action_execs.append(
                await provider.get_repository(ActionExecution).create(action_exec)
            )

        control_execution.action_execution_ids = [str(i.id) for i in action_execs]
        await provider.get_repository(ControlExecution).update(control_execution)
    return control_execution, action_execs


async def run_graph_by_execution_id(
    control_execution_id: UUID,
    credentials: List[Dict[str, CredentialValue]],
    run_step_by_step: bool = False,
    allow_rerun: bool = False,
):
    if RQ_BACKGROUND_TASKS_ENABLED:
        initialize_worker_dependencies()

    async with get_provider() as async_provider:
        control_exec = await async_provider.get_repository(ControlExecution).get(
            control_execution_id
        )
        if not control_exec:
            raise ControlExecutionNotFoundException("ControlExecution not found")

        action_execs: List[ActionExecution] = []
        for action_exec_id in control_exec.action_execution_ids:
            action_exec = await async_provider.get_repository(ActionExecution).get(
                action_exec_id
            )
            if not action_exec:
                raise ValueError(f"ActionExecution with id {action_exec_id} not found")
            action_execs.append(action_exec)

        action_execs = sorted(action_execs, key=lambda x: x.order)

        nodes = get_nodes_from_strings([i.action_prototype_name for i in action_execs])
        action_control_variables_list = [
            i.control_variables | i.reference_variables | i.independent_variables
            for i in action_execs
        ]

    await run_graph(
        nodes=nodes,
        action_deps_list=action_control_variables_list,
        control_exec_id=control_execution_id,
        step_by_step=run_step_by_step,
        allow_rerun=allow_rerun,
        credentials=credentials,
    )


async def resume_graph_by_execution_id(
    control_execution_id: UUID,
    extra_instructions: str,
    credentials: List[Dict[str, CredentialValue]],
    resume_step_by_step: bool = False,
):
    if RQ_BACKGROUND_TASKS_ENABLED:
        initialize_worker_dependencies()

    async with get_provider() as async_provider:
        control_exec = await async_provider.get_repository(ControlExecution).get(
            control_execution_id
        )
        if not control_exec:
            raise ControlExecutionNotFoundException("ControlExecution not found")

        action_execs: List[ActionExecution] = []
        for action_exec_id in control_exec.action_execution_ids:
            action_exec = await async_provider.get_repository(ActionExecution).get(
                action_exec_id
            )
            if not action_exec:
                raise ValueError(f"ActionExecution with id {action_exec_id} not found")
            action_execs.append(action_exec)

        action_execs = sorted(action_execs, key=lambda x: x.order)

        nodes = get_nodes_from_strings([i.action_prototype_name for i in action_execs])
        action_control_variables_list = [
            i.control_variables | i.reference_variables | i.independent_variables
            for i in action_execs
        ]
    await resume_graph(
        nodes=nodes,
        action_deps_list=action_control_variables_list,
        control_exec_id=control_execution_id,
        extra_instructions=extra_instructions,
        step_by_step=resume_step_by_step,
        credentials=credentials,
    )


async def execute_control(
    exec_request: PostControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks,
    run_step_by_step: bool = False,
) -> tuple[ControlExecution, List[ActionExecution]]:
    """
    ** Will be deprecated, call create, run separately to make the process more clear.**

    Execute a control with all its stored execution args.
    1. create control execution and its actions
    2. run control execution

    This function will always allow rerun without protection.

    Args:
        exec_request: The request to execute the control
        background_tasks: FastAPI background tasks

    Returns:
        ControlExecution and ActionExecution list
    """
    control_execution, action_execs = await upsert_control_execution(exec_request)
    if isinstance(background_tasks, QueuedBackgroundTasks):
        background_tasks.add_task(
            run_graph_by_execution_id,
            control_execution_id=control_execution.id,
            run_step_by_step=run_step_by_step,
            allow_rerun=True,
            job_id=str(control_execution.id),
            timeout=3600,  # 1 hour
            credentials=exec_request.credentials,
        )
    else:
        background_tasks.add_task(
            run_graph_by_execution_id,
            control_execution_id=control_execution.id,
            run_step_by_step=run_step_by_step,
            allow_rerun=True,
            credentials=exec_request.credentials,
        )

    return control_execution, action_execs


async def get_control_execution(
    control_execution_id: UUID, provider: RepositoryProvider
) -> GetControlExecutionStatusResponse:
    control_repo = provider.get_repository(ControlExecution)
    control_execution: ControlExecution | None = await control_repo.get(
        control_execution_id
    )
    if not control_execution:
        raise ControlExecutionNotFoundException(
            f"ControlExecution with id {control_execution_id} not found"
        )

    # action_exec_history records the index of the action execution in the action_execution_ids list
    # this part means we only return the action execution ids that are in the action_exec_history list
    action_exec_history_ids = []
    if control_execution.action_exec_history:
        action_exec_history_ids = [
            control_execution.action_execution_ids[ind]
            for ind in control_execution.action_exec_history
        ]
    return GetControlExecutionStatusResponse(
        id=control_execution.id,
        control_id=control_execution.control_id,
        created_at=control_execution.created_at,
        updated_at=control_execution.updated_at,
        status=control_execution.status,
        output=control_execution.output,
        error=control_execution.error_message,
        log=control_execution.log,
        action_exec_history_ids=action_exec_history_ids,
    )


def _run_graph_by_execution_id_sync(
    control_execution_id: UUID, credentials: List[Dict[str, CredentialValue]]
) -> None:
    """
    Synchronous wrapper for run_graph_by_execution_id that can be called by the scheduler.

    Args:
        control_execution_id: The UUID of the control execution to run
        credentials: The credentials to use for the control execution
    """
    import asyncio

    # Run the async function in a new event loop
    asyncio.run(run_graph_by_execution_id(control_execution_id, credentials))


def create_delayed_control_execution_job(
    control_execution_id: UUID,
    credentials: List[Dict[str, CredentialValue]],
    delay_seconds: int = 15,
) -> str:
    """
    Create a delayed job that reruns a control execution after a specified delay.

    Args:
        control_execution_id: The UUID of the control execution to rerun
        delay_seconds: Number of seconds to wait before rerunning (default: 15)

    Returns:
        The job ID of the created delayed job
    """
    from datetime import datetime, timedelta

    from apscheduler.triggers.date import DateTrigger

    from app.utils.scheduler.scheduler import get_scheduler

    scheduler = get_scheduler()

    job_id = f"delayed_control_exec_{control_execution_id}"

    # Calculate the future execution time
    future_time = datetime.now() + timedelta(seconds=delay_seconds)

    # Add the job to run after the delay using the sync wrapper
    scheduler.add_job(
        func=_run_graph_by_execution_id_sync,
        trigger=DateTrigger(run_date=future_time),
        id=job_id,
        name=f"Delayed Control Execution {control_execution_id}",
        args=(control_execution_id, credentials),
        replace_existing=True,  # Replace if job already exists
    )

    logfire.info(
        "Created delayed control execution job",
        control_execution_id=str(control_execution_id),
        job_id=job_id,
        delay_seconds=delay_seconds,
        scheduled_time=future_time.isoformat(),
    )

    return job_id


def cancel_delayed_control_execution_jobs(control_execution_id: UUID) -> int:
    """
    Cancel all delayed jobs for a control execution.

    Args:
        control_execution_id: The UUID of the control execution

    Returns:
        Number of jobs that were successfully cancelled
    """
    from app.utils.scheduler.scheduler import get_scheduler

    scheduler = get_scheduler()
    return scheduler.cancel_delayed_control_execution_jobs(str(control_execution_id))


def get_delayed_control_execution_jobs() -> list:
    """
    Get all delayed control execution jobs.

    Returns:
        List of delayed control execution jobs
    """
    from app.utils.scheduler.scheduler import get_scheduler

    scheduler = get_scheduler()
    return scheduler.get_delayed_control_execution_jobs()


def get_control_execution_job_status(control_execution_id: UUID) -> dict:
    """
    Get the status of delayed control execution jobs for a specific control execution.

    Args:
        control_execution_id: The UUID of the control execution

    Returns:
        Dictionary with job status information
    """
    from app.utils.scheduler.scheduler import get_scheduler

    scheduler = get_scheduler()
    jobs = scheduler.get_delayed_control_execution_jobs_for_control_execution(
        str(control_execution_id)
    )

    if jobs:
        return {
            "exists": True,
            "job_count": len(jobs),
            "jobs": [
                {
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
                for job in jobs
            ],
        }
    else:
        return {"exists": False, "job_count": 0, "jobs": []}


async def reset_control_execution_head_to_index(
    request: ResetControlExecutionHeadToIndexRequest,
) -> ResetControlExecutionHeadToIndexResponse:
    """Reset the head of a control execution to a specific index.

    Args:
        request: The rerun request with control_execution_id, start_from and optional overwrite_state
        background_tasks: FastAPI background tasks

    Returns:
        RerunControlExecutionResponse with control_execution_id and queued status
    """
    async with get_provider() as provider:
        # Validate control execution exists
        control_exec = await provider.get_repository(ControlExecution).get(
            request.control_execution_id
        )
        if not control_exec:
            raise ControlExecutionNotFoundException(
                f"ControlExecution with id {request.control_execution_id} not found"
            )
        control_exec.current_action_index = request.reset_to
        await provider.get_repository(ControlExecution).update(control_exec)

        if not control_exec:
            raise ControlExecutionNotFoundException(
                f"ControlExecution with id {request.control_execution_id} not found"
            )

        # Normalize overwrite_state
        overwrite_state_dict: dict[str, Any] | None = None
        if request.overwrite_state:
            if isinstance(request.overwrite_state, list):
                if len(request.overwrite_state) > 0:
                    overwrite_state_dict = {}
                    for d in request.overwrite_state:
                        if isinstance(d, dict):
                            overwrite_state_dict.update(d)
                else:
                    overwrite_state_dict = None
            else:
                overwrite_state_dict = request.overwrite_state
        # Prepare in-place rerun
        logfire.info(
            "Preparing in-place rerun",
            graph_id=str(request.control_execution_id),
            start_index=request.reset_to,
        )

        SqlStatePersistence.rerun_inplace(
            graph_id=str(request.control_execution_id),
            start_index=request.reset_to,
            connection_string=SQLITE_DATABASE_SYNC_URL,
            overwrite_state=overwrite_state_dict,
        )

        # setup provision of control execution folder
        setup_control_execution_folder_for_rerun(
            control_execution_folder=construct_control_execution_folder(
                control_exec.control_id,
                control_exec.entity_id,
                request.control_execution_id,
            ),
            start_index=request.reset_to,
        )

        # remove the steps after the target action execution index
        target_step = 0
        for i in control_exec.action_exec_history:
            if i == request.reset_to:
                break
            target_step += 1
        control_exec.reset_action_exec_history(target_step)
        await provider.get_repository(ControlExecution).update(control_exec)

    return ResetControlExecutionHeadToIndexResponse(
        control_execution_id=request.control_execution_id,
        current_head_index=control_exec.current_action_index,
    )


async def create_control_only(
    exec_request: PostControlExecutionRequest,
) -> tuple[ControlExecution, List[ActionExecution]]:
    """Create or update a control execution and its actions without running it."""
    control_execution, action_execs = await upsert_control_execution(exec_request)
    return control_execution, action_execs


async def run_control_only(
    request: RunControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks,
) -> RunControlExecutionResponse:
    """Queue running of an existing control execution."""
    if isinstance(background_tasks, QueuedBackgroundTasks):
        background_tasks.add_task(
            run_graph_by_execution_id,
            control_execution_id=request.control_execution_id,
            credentials=request.credentials,
            run_step_by_step=request.run_step_by_step,
            job_id=str(request.control_execution_id),
            timeout=3600,  # 1 hour
        )
    else:
        background_tasks.add_task(
            run_graph_by_execution_id,
            control_execution_id=request.control_execution_id,
            run_step_by_step=request.run_step_by_step,
            credentials=request.credentials,
        )
    return RunControlExecutionResponse(
        control_execution_id=request.control_execution_id,
        run_step_by_step=request.run_step_by_step,
    )


async def resume_control_execution(
    request: ResumeControlExecutionRequest,
    background_tasks: QueuedBackgroundTasks | BackgroundTasks,
) -> ResumeControlExecutionResponse:
    """Queue resuming of an existing control execution."""
    if isinstance(background_tasks, QueuedBackgroundTasks):
        background_tasks.add_task(
            resume_graph_by_execution_id,
            control_execution_id=request.control_execution_id,
            extra_instructions=request.extra_instructions or "",
            resume_step_by_step=request.resume_step_by_step,
            job_id=str(request.control_execution_id),
            timeout=3600,  # 1 hour
            credentials=request.credentials,
        )
    else:
        background_tasks.add_task(
            resume_graph_by_execution_id,
            control_execution_id=request.control_execution_id,
            extra_instructions=request.extra_instructions or "",
            resume_step_by_step=request.resume_step_by_step,
            credentials=request.credentials,
        )
    return ResumeControlExecutionResponse(
        control_execution_id=request.control_execution_id,
        resume_step_by_step=request.resume_step_by_step,
        extra_instructions=request.extra_instructions,
    )
