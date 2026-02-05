from alltrue.queue.task import QueuedBackgroundTasks, QueuedTasks
from fastapi import BackgroundTasks

from app.utils.queue import get_queue_manager
from config import RQ_BACKGROUND_TASKS_ENABLED


def get_background_tasks(
    background_tasks: BackgroundTasks,
) -> QueuedBackgroundTasks | BackgroundTasks:
    if RQ_BACKGROUND_TASKS_ENABLED:
        return QueuedBackgroundTasks(QueuedTasks(get_queue_manager()), background_tasks)
    else:
        return background_tasks
