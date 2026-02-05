from pathlib import Path
from typing import Dict, List, Optional, Union
from uuid import UUID

import logfire
from alltrue.agents.schema.action_execution import (
    ActionExecutionStatus,
    LogEntry,
    ObjectLog,
    PlainTextLog,
)
from alltrue.agents.schema.customer_credential import CredentialValue
from pydantic import ConfigDict, Field

from app.core.graph.deps.base_deps import BaseDeps


class ActionDeps(BaseDeps):
    action_id: UUID
    action_name: str
    node_ind: int
    write_db_log: bool = True
    credentials: Dict[str, CredentialValue] = Field(default_factory=dict)
    action_folder_name: Optional[str] = None
    action_working_dir: Optional[str] = None

    model_config = ConfigDict(extra="allow")

    # Initialization and cleanup methods
    def model_post_init(self, __context):
        super().model_post_init(__context)
        if self.working_dir is None:
            raise ValueError("working_dir is not set")
        if self.action_folder_name is None:
            self.action_folder_name = f"{self.action_name}_{self.node_ind}"
        if self.action_working_dir is None:
            self.action_working_dir = str(
                (Path(self.working_dir) / self.action_folder_name).resolve()
            )
            Path(self.action_working_dir).mkdir(parents=True, exist_ok=True)

    async def add_log(
        self,
        log: Union[PlainTextLog, ObjectLog, List[PlainTextLog | ObjectLog]],
    ):
        """
        Adds a log entry by fetching the model, updating it, and saving it back.
        """
        logfire.info(f"Adding log", log=log)
        if not self.write_db_log:
            logfire.warning("write_db_log is false, skipping log.")
            return

        # 1. GET the current state from the repository
        action_exec = await self.action_repo.get(self.action_id)
        if not action_exec:
            logfire.error(f"ActionExecution {self.action_id} not found to add log.")
            return

        # 2. MODIFY the model object in memory
        if not isinstance(log, list):
            log = [log]

        # We need to create a proper LogEntry object if that's what your model expects
        log_entry = LogEntry(content=log)  # Assuming LogEntry structure
        action_exec.add_log(log_entry)

        # 3. UPDATE the repository with the modified object
        await self.action_repo.update(action_exec)

    async def update_action_status(
        self,
        status: ActionExecutionStatus,
        **kwargs,
    ):
        """
        Updates the action status using the get -> modify -> update pattern.
        """
        logfire.info(f"Updating action status", status=status, kwargs=kwargs)
        if not self.write_db_log or self.action_repo is None:
            logfire.warning(
                "No action repo or write_db_log is false, skipping status update."
            )
            return

        # 1. GET the current state from the repository
        action_exec = await self.action_repo.get(self.action_id)
        if not action_exec:
            logfire.error(
                f"ActionExecution {self.action_id} not found to update status."
            )
            return

        # 2. MODIFY the model by calling its own business logic methods
        if status == ActionExecutionStatus.IN_PROGRESS:
            action_exec.mark_in_progress(
                kwargs.get(
                    "message",
                    f"Action: {action_exec.action_prototype_name}, Execution In Progress",
                )
            )
        elif status == ActionExecutionStatus.PASSED:
            action_exec.mark_passed(
                output=kwargs["output"],
                message=kwargs.get("message", "Execution completed successfully"),
            )
        elif status == ActionExecutionStatus.ACTION_REQUIRED:
            action_exec.mark_action_required(kwargs["error"])
        elif status == ActionExecutionStatus.REMEDIATION_REQUIRED:
            action_exec.mark_remediation_required(kwargs["error"])
        elif status == ActionExecutionStatus.FAILED:
            action_exec.mark_failed(kwargs["error"])
        else:
            logfire.error(f"Unknown status: {status}")
            return

        # 3. UPDATE the repository with the modified object
        await self.action_repo.update(action_exec)


class ToolActionDeps(ActionDeps):
    selected_model: Optional[str] = None
