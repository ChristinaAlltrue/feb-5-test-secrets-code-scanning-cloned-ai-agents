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
import logfire
from alltrue import queue
from alltrue.queue.manager import QueueManager

_QM_CONFIG_KEY = "ai-agents-redis-queue"
_QUEUE_MANAGER: QueueManager | None = None


@logfire.instrument()
def get_queue_manager() -> QueueManager:
    global _QUEUE_MANAGER
    if _QUEUE_MANAGER is None:
        # first, connect to configured instance
        _QUEUE_MANAGER = queue.connect_queue_manager(
            config_key=_QM_CONFIG_KEY,
        )
        if _QUEUE_MANAGER is None:
            logfire.warn(
                """
                !!! No Connection Available for QueueManager, FakeRedis Will Be Used !!!
                """
            )
            from fakeredis import FakeRedis
            from rq.worker import SimpleWorker

            _QUEUE_MANAGER = queue.connect_queue_manager(
                config_key=_QM_CONFIG_KEY,
                connection=FakeRedis(),
                worker_class=SimpleWorker,
                is_async=False,
            )
    return _QUEUE_MANAGER


@logfire.instrument()
def stop_queue_manager():
    global _QUEUE_MANAGER
    if _QUEUE_MANAGER is not None:
        _QUEUE_MANAGER.stop_workers()
        _QUEUE_MANAGER = None
