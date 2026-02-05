from alltrue.queue.task import QueuedBackgroundTasks
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.core.app import ROOT_PATH
from app.api.dependencies.queue_manager import get_background_tasks

router = APIRouter()


@router.get("/", status_code=200)
def root():
    # redirect to docs
    return RedirectResponse(url=f"{ROOT_PATH}/docs")


def job_queue_test_task(test_message: str):
    print(f"Job queue test task executed: {test_message}")


@router.get("/job-queue-test", status_code=200)
def job_queue_test(
    background_tasks: QueuedBackgroundTasks = Depends(get_background_tasks),
):
    background_tasks.add_task(job_queue_test_task, test_message="Hello, world!")
    return "Job queue test"


@router.get("/health", status_code=200)
def healthcheck():
    return "I am healthy"
