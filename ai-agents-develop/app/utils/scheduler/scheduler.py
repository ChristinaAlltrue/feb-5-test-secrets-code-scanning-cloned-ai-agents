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

import os
from typing import Any, Dict, Optional

import logfire
from apscheduler.executors.asyncio import AsyncIOExecutor  # type: ignore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger


class SchedulerService:
    """Service for managing background job scheduling using APScheduler."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the scheduler service.

        Args:
            database_url: SQLite database URL for job persistence.
                         Defaults to 'sqlite:///scheduler.db' in the project root.
        """
        if database_url is None:
            # Use project root directory for the database file
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            database_path = os.path.join(project_root, "scheduler.db")
            database_url = f"sqlite:///{database_path}"

        # Configure job store with SQLite
        jobstores = {"default": SQLAlchemyJobStore(url=database_url)}

        # Configure executors with AsyncIOExecutor for async functions
        executors = {"default": AsyncIOExecutor()}

        # Job defaults
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 15,  # seconds
        }

        # Initialize the scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )

        self._is_running = False
        logfire.info("SchedulerService initialized", database_url=database_url)

    async def start(self) -> None:
        """Start the scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logfire.info("Scheduler started successfully")
        else:
            logfire.warning("Scheduler is already running")

    async def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logfire.info("Scheduler shutdown completed")
        else:
            logfire.warning("Scheduler is not running")

    def add_job(
        self,
        func: Any,
        trigger: BaseTrigger,
        id: Optional[str] = None,
        name: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        replace_existing: bool = False,
        **trigger_args: Any,
    ) -> str:
        """
        Add a job to the scheduler.

        Args:
            func: The callable to execute
            trigger: The trigger for the job
            id: Unique identifier for the job
            name: Human readable name for the job
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            replace_existing: Whether to replace existing job with same id
            **trigger_args: Additional trigger arguments

        Returns:
            The job ID
        """
        logfire.info(f"Adding job {id}: {name} to scheduler")
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=id,
            name=name,
            args=args,
            kwargs=kwargs,
            replace_existing=replace_existing,
            **trigger_args,
        )

        logfire.info(
            "Job added to scheduler",
            job_id=job.id,
            job_name=name,
            trigger_type=type(trigger).__name__,
        )

        return job.id

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler."""
        self.scheduler.remove_job(job_id)
        logfire.info("Job removed from scheduler", job_id=job_id)

    def get_job(self, job_id: str) -> Optional[Any]:
        """Get a job by its ID."""
        return self.scheduler.get_job(job_id)

    def get_jobs(self) -> list:
        """Get all jobs."""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str) -> None:
        """Pause a job."""
        self.scheduler.pause_job(job_id)
        logfire.info("Job paused", job_id=job_id)

    def resume_job(self, job_id: str) -> None:
        """Resume a paused job."""
        self.scheduler.resume_job(job_id)
        logfire.info("Job resumed", job_id=job_id)

    def get_delayed_control_execution_jobs(self) -> list:
        """Get all delayed control execution jobs."""
        jobs = self.get_jobs()
        delayed_jobs = []
        for job in jobs:
            if job.id and job.id.startswith("delayed_control_exec_"):
                delayed_jobs.append(job)
        return delayed_jobs

    def get_delayed_control_execution_jobs_for_control_execution(
        self, control_execution_id: str
    ) -> list:
        """Get all delayed control execution jobs for a specific control execution ID."""
        jobs = self.get_jobs()
        control_exec_jobs = []
        for job in jobs:
            if job.id and job.id.startswith(
                f"delayed_control_exec_{control_execution_id}_"
            ):
                control_exec_jobs.append(job)
        return control_exec_jobs

    def cancel_delayed_control_execution_jobs(self, control_execution_id: str) -> int:
        """Cancel all delayed control execution jobs for a specific control execution ID."""
        jobs = self.get_delayed_control_execution_jobs_for_control_execution(
            control_execution_id
        )
        cancelled_count = 0

        for job in jobs:
            try:
                self.remove_job(job.id)
                logfire.info("Cancelled delayed control execution job", job_id=job.id)
                cancelled_count += 1
            except Exception as e:
                logfire.error(
                    "Failed to cancel delayed control execution job",
                    job_id=job.id,
                    error=str(e),
                )

        if cancelled_count == 0:
            logfire.warning(
                "No delayed control execution jobs found to cancel",
                control_execution_id=control_execution_id,
            )

        return cancelled_count

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._is_running


# Global scheduler instance - singleton pattern
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """
    Get the global scheduler service instance.

    This is the main function to call from anywhere in your code to access the scheduler.

    Returns:
        SchedulerService: The scheduler service instance

    Raises:
        RuntimeError: If the scheduler service is not initialized
    """
    global _scheduler_service
    if _scheduler_service is None:
        raise RuntimeError(
            "Scheduler service not initialized. Make sure the FastAPI app has started."
        )
    return _scheduler_service


async def initialize_scheduler(database_url: Optional[str] = None) -> SchedulerService:
    """
    Initialize the global scheduler service.

    This is called automatically during FastAPI lifespan startup.

    Args:
        database_url: Optional custom database URL

    Returns:
        SchedulerService: The initialized scheduler service
    """
    global _scheduler_service
    if _scheduler_service is not None:
        logfire.warning("Scheduler service already initialized")
        return _scheduler_service

    _scheduler_service = SchedulerService(database_url)
    await _scheduler_service.start()
    return _scheduler_service


async def shutdown_scheduler() -> None:
    """
    Shutdown the global scheduler service.

    This is called automatically during FastAPI lifespan shutdown.
    """
    global _scheduler_service
    if _scheduler_service is not None:
        await _scheduler_service.shutdown()
        _scheduler_service = None
