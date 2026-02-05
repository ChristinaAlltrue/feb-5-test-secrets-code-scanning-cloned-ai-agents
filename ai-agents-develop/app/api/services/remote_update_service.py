import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import httpx
import logfire
from alltrue.agents.schema.control_plane_service import (
    AgentActionExecutionUpdate,
    AgentControlEntityExecutionUpdate,
)
from alltrue.client import Client
from alltrue.client.requests import _make_headers, make_full_url
from alltrue.local.authorization.internal_token import get_internal_access_token
from apscheduler.triggers.date import DateTrigger

from app.core.models.models import ActionExecution, ControlExecution
from app.utils.scheduler.scheduler import get_scheduler

MAX_RETRY_DELAY_SECONDS = 60.0
MAX_RETRY_COUNT = 100  # we want it synced to CP eventually, just a big number to avoid infinite retries


def retry_seconds(retry_count: int) -> float:
    """
    Calculate the number of seconds to wait before retrying the update.
    """
    return min(5.0 + math.pow(2, retry_count), MAX_RETRY_DELAY_SECONDS)


class RemoteUpdateService(ABC):
    """Abstract base class for remote update services."""

    @abstractmethod
    async def patch_action_execution(self, action_exec: ActionExecution) -> None:
        """Update action execution status on remote service.

        Args:
            action_exec: The action execution to update
        """

    @abstractmethod
    async def patch_control_execution(self, control_exec: ControlExecution) -> None:
        """Update control execution status on remote service.

        Args:
            control_exec: The control execution to update
        """


class ControlPlaneUpdateService(RemoteUpdateService):
    """Update service for control plane."""

    def __init__(self):
        # Workaround to renew the new token everytime it calls the control plane to avoid the token expiration
        # TODO: move this to python security api repo
        pass

    async def patch_action_execution(self, action_exec: ActionExecution) -> None:
        """Update action execution status on remote service."""
        self.client = Client(
            access_token=get_internal_access_token(), internal_access=True
        ).control_plane()
        full_url = make_full_url(
            self.client.client_config, "control-plane/ai-agents/action-execution"
        )
        default_headers = _make_headers(self.client.client_config)

        update_payload = AgentActionExecutionUpdate(
            id=action_exec.id,
            status=action_exec.status,
            log=action_exec.log,
            error_message=action_exec.error_message,
            output=action_exec.output,
            updated_at=action_exec.updated_at,
        )
        try:
            async with httpx.AsyncClient(
                verify=self.client.client_config.verify_ssl,
                timeout=httpx.Timeout(10.0, connect=5.0),
            ) as cp_client:
                response = await cp_client.patch(
                    full_url,
                    json=update_payload.model_dump(exclude_none=True, mode="json"),
                    headers=default_headers,
                )
                status_code = response.status_code
                if 200 <= status_code < 300:
                    return
                elif status_code == 400:
                    logfire.error(
                        f"id not found, skip patching action execution {update_payload.id}"
                    )
                    return
                else:
                    raise Exception(
                        f"Error updating action execution {update_payload.id}: {response.text}"
                    )
        except Exception as e:
            logfire.error(f"Error updating action execution {update_payload.id}: {e}")
            scheduler = get_scheduler()
            scheduler.add_job(
                func=ControlPlaneUpdateService.retry_patch_action_execution,
                trigger=DateTrigger(
                    run_date=datetime.now(timezone.utc)
                    + timedelta(seconds=retry_seconds(0))
                ),
                args=(update_payload, 0),
                id=f"action_exec_retry_{update_payload.id}",
                name=f"Action Execution Retry {update_payload.id}",
                replace_existing=True,
            )
            # let scheduler handle the retry
            return

    async def patch_control_execution(self, control_exec: ControlExecution) -> None:
        """Update control execution status on remote service."""
        self.client = Client(
            access_token=get_internal_access_token(), internal_access=True
        ).control_plane()
        full_url = make_full_url(
            self.client.client_config,
            "control-plane/ai-agents/control-entity-execution",
        )
        default_headers = _make_headers(self.client.client_config)

        update_payload = AgentControlEntityExecutionUpdate(
            id=control_exec.id,
            status=control_exec.status,
            log=control_exec.log,
            output=control_exec.output,
            updated_at=control_exec.updated_at,
            action_exec_history=control_exec.action_exec_history,
            compliance_status=control_exec.compliance_status,
        )
        try:
            async with httpx.AsyncClient(
                verify=self.client.client_config.verify_ssl,
                timeout=httpx.Timeout(10.0, connect=5.0),
            ) as cp_client:
                response = await cp_client.patch(
                    full_url,
                    json=update_payload.model_dump(exclude_none=True, mode="json"),
                    headers=default_headers,
                )
                status_code = response.status_code
                if 200 <= status_code < 300:
                    return
                elif status_code == 400:
                    logfire.error(
                        f"id not found, skip patching control execution {update_payload.id}"
                    )
                    return
                else:
                    raise Exception(
                        f"Error updating control execution {update_payload.id}: {response.text}"
                    )

        except Exception as e:
            logfire.error(f"Error updating control execution {update_payload.id}: {e}")
            scheduler = get_scheduler()
            scheduler.add_job(
                func=ControlPlaneUpdateService.retry_patch_control_execution,
                trigger=DateTrigger(
                    run_date=datetime.now(timezone.utc)
                    + timedelta(seconds=retry_seconds(0))
                ),
                args=(update_payload, 0),
                id=f"control_exec_retry_{update_payload.id}",
                name=f"Control Execution Retry {update_payload.id}",
                replace_existing=True,
            )
            # let scheduler handle the retry
            return

    @staticmethod
    def retry_patch_control_execution(
        update_payload: AgentControlEntityExecutionUpdate, retry_count: int
    ) -> None:
        """Retry updating control execution status on remote service."""
        retry_count += 1
        if retry_count > MAX_RETRY_COUNT:
            logfire.error(
                f"Max retry count reached for control execution {update_payload.id}, skipping retry"
            )
            return

        logfire.info(
            f"Retry updating control execution {update_payload.id} (retry count: {retry_count})"
        )
        client = Client(
            access_token=get_internal_access_token(), internal_access=True
        ).control_plane()
        full_url = make_full_url(
            client.client_config,
            "control-plane/ai-agents/control-entity-execution",
        )
        default_headers = _make_headers(client.client_config)
        try:
            with httpx.Client(
                verify=client.client_config.verify_ssl,
                timeout=httpx.Timeout(10.0, connect=5.0),
            ) as cp_client:
                response = cp_client.patch(
                    full_url,
                    json=update_payload.model_dump(exclude_none=True, mode="json"),
                    headers=default_headers,
                )
                status_code = response.status_code
                if 200 <= status_code < 300:
                    logfire.info(
                        f"Control execution {update_payload.id} updated successfully"
                    )
                    return
                elif status_code == 400:
                    logfire.error(
                        f"id not found, skip patching control execution {update_payload.id}"
                    )
                    return
                else:
                    raise Exception(
                        f"Error updating control execution {update_payload.id}: {response.text}"
                    )
        except Exception as e:
            logfire.error(f"Error updating control execution {update_payload.id}: {e}")
            scheduler = get_scheduler()
            scheduler.add_job(
                func=ControlPlaneUpdateService.retry_patch_control_execution,
                trigger=DateTrigger(
                    run_date=datetime.now(timezone.utc)
                    + timedelta(seconds=retry_seconds(retry_count))
                ),
                args=(update_payload, retry_count),
                id=f"control_exec_retry_{update_payload.id}",
                name=f"Control Execution Retry {update_payload.id}",
                replace_existing=True,
            )
            return

    @staticmethod
    def retry_patch_action_execution(
        update_payload: AgentActionExecutionUpdate, retry_count: int
    ) -> None:
        """Retry updating action execution status on remote service."""
        retry_count += 1
        if retry_count > MAX_RETRY_COUNT:
            logfire.error(
                f"Max retry count reached for action execution {update_payload.id}, skipping retry"
            )
            return

        logfire.info(
            f"Retry updating action execution {update_payload.id} (retry count: {retry_count})"
        )
        client = Client(
            access_token=get_internal_access_token(), internal_access=True
        ).control_plane()
        full_url = make_full_url(
            client.client_config,
            "control-plane/ai-agents/action-execution",
        )
        default_headers = _make_headers(client.client_config)
        try:
            with httpx.Client(
                verify=client.client_config.verify_ssl,
                timeout=httpx.Timeout(10.0, connect=5.0),
            ) as cp_client:
                response = cp_client.patch(
                    full_url,
                    json=update_payload.model_dump(exclude_none=True, mode="json"),
                    headers=default_headers,
                )
                status_code = response.status_code
                if 200 <= status_code < 300:
                    logfire.info(
                        f"Action execution {update_payload.id} updated successfully"
                    )
                    return
                elif status_code == 400:
                    logfire.error(
                        f"id not found, skip patching action execution {update_payload.id}"
                    )
                    return
                else:
                    raise Exception(
                        f"Error updating action execution {update_payload.id}: {response.text}"
                    )
        except Exception as e:
            logfire.error(f"Error updating action execution {update_payload.id}: {e}")
            scheduler = get_scheduler()
            scheduler.add_job(
                func=ControlPlaneUpdateService.retry_patch_action_execution,
                trigger=DateTrigger(
                    run_date=datetime.now(timezone.utc)
                    + timedelta(seconds=retry_seconds(retry_count))
                ),
                args=(update_payload, retry_count),
                id=f"action_exec_retry_{update_payload.id}",
                name=f"Action Execution Retry {update_payload.id}",
                replace_existing=True,
            )
            return
