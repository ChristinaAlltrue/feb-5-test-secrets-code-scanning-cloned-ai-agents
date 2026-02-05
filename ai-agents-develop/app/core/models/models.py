import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type

import logfire
from alltrue.agents.schema.action_execution import (
    ActionExecutionStatus,
    LogEntry,
    PlainTextLog,
)
from alltrue.agents.schema.control_execution import (
    ComplianceStatus,
    ControlExecutionStatus,
)
from sqlalchemy import JSON, Column, Integer, Text
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Field, SQLModel

from app.core.models.types import uuid_column

# Module-level event handler registry
_event_handlers: Dict[Type[SQLModel], List[Callable[[Any, str], None]]] = {}


def register_event_handler(
    model_class: Type[SQLModel], handler: Callable[[Any, str], None]
):
    """Register an event handler for a model class."""
    if model_class not in _event_handlers:
        _event_handlers[model_class] = []
    _event_handlers[model_class].append(handler)


def trigger_event(instance: Any, event_type: str):
    """Trigger events for an instance."""
    model_class = type(instance)
    if model_class in _event_handlers:
        for handler in _event_handlers[model_class]:
            try:
                handler(instance, event_type)
            except Exception as e:
                logfire.error(
                    f"Event handler failed for {model_class.__name__}", error=str(e)
                )


class ActionExecution(SQLModel, table=True):  # type: ignore[call-arg]
    """
    ActionExecution's unified model.
    It is both a Pydantic model and a SQLAlchemy table.
    """

    __tablename__ = "action_execution"

    # Map to Control Plane AgentActionExecution.id
    id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(primary_key=True),
    )

    action_prototype_name: str = Field(sa_column=Column(Text, nullable=False))
    order: int
    # Map to Control Plane AgentActionExecution.agent_control_entity_execution_id
    control_execution_id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(foreign_key="control_execution.id", nullable=False),
    )

    status: ActionExecutionStatus = Field(
        default=ActionExecutionStatus.PENDING, nullable=False
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    # Map to Control Plane AgentActionExecution.log
    log: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))

    output: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Use the generic JSON type instead of JSONB
    control_variables: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    reference_variables: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    independent_variables: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    subagents: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )

    @classmethod
    def register_event_handler(cls, handler):
        register_event_handler(cls, handler)

    def _update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    def reset(self):
        self.status = ActionExecutionStatus.PENDING
        self.error_message = None
        self.output = {}
        self.log = []
        self._update_timestamp()
        trigger_event(self, "update")

    def add_log(self, entry: LogEntry):
        if self.log is None:
            self.log = []
        self.log.append(entry.model_dump())
        flag_modified(self, "log")
        self._update_timestamp()
        trigger_event(self, "update")

    def _set_status_and_log(self, status: ActionExecutionStatus, message: str):
        self.status = status
        log_entry = LogEntry(
            content=[PlainTextLog(data=message)],
        )
        self.add_log(log_entry)

    def mark_in_progress(self, message: str = "Action: Execution started"):
        self._set_status_and_log(ActionExecutionStatus.IN_PROGRESS, message=message)

    def mark_passed(
        self, output: dict, message: str = "Execution completed successfully"
    ):
        self.output = output
        self._set_status_and_log(ActionExecutionStatus.PASSED, message=message)

    def mark_action_required(self, error: str):
        """
        Action required means the error is in the agent itself. Agent cannot execute because of the parameter error or other internal error.
        """
        self.error_message = error
        self._set_status_and_log(
            ActionExecutionStatus.ACTION_REQUIRED, message=f"Action required: {error}"
        )

    def mark_remediation_required(self, error: str):
        """
        Remediation required means the error comes from outside of agent. Agent can execute successfully but the result is not qualified.
        """
        self.error_message = error
        self._set_status_and_log(
            ActionExecutionStatus.REMEDIATION_REQUIRED,
            message=f"Remediation required: {error}",
        )

    def mark_failed(self, error: str):
        self.error_message = error
        self._set_status_and_log(
            ActionExecutionStatus.FAILED, message=f"Failed: {error}"
        )


class ControlExecution(SQLModel, table=True):  # type: ignore[call-arg]
    """
    ControlExecution's unified model.
    """

    __tablename__ = "control_execution"

    id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(primary_key=True),
    )
    customer_id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(nullable=False),
    )
    current_action_index: int = Field(
        default=0, sa_column=Column(Integer, nullable=False)
    )

    control_id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(nullable=False),
    )
    entity_id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(),
        sa_column=uuid_column(nullable=False),
    )
    compliance_instruction: str = Field(
        default="", sa_column=Column(Text, nullable=False)
    )
    # Use the generic JSON type instead of JSONB
    action_execution_ids: List[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )  # use str to make it compatible with redis and sqlite

    entity_exec_args: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    action_exec_history: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    edges: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))

    compliance_status: Optional[ComplianceStatus] = Field(
        default=ComplianceStatus.PENDING, nullable=False
    )
    output: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    log: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))

    status: ControlExecutionStatus = Field(
        default=ControlExecutionStatus.PENDING, nullable=False
    )
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    @classmethod
    def register_event_handler(cls, handler):
        register_event_handler(cls, handler)

    @property
    def action_execution_uuids(self) -> List[uuid.UUID]:
        """
        Parses the raw string IDs from `action_execution_ids` and returns
        them as a list of actual UUID objects.
        """
        return [uuid.UUID(aid_str) for aid_str in self.action_execution_ids]

    def _update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    def reset(self):
        self.status = ControlExecutionStatus.PENDING
        self.compliance_status = ComplianceStatus.PENDING
        self.error_message = None
        self.output = {}
        self.log = []
        self.action_exec_history = []
        self.current_action_index = 0
        self._update_timestamp()
        trigger_event(self, "update")

    def add_log(self, message: str):
        log_entry = LogEntry(
            content=[PlainTextLog(data=message)],
        )
        self.log.append(log_entry.model_dump())
        flag_modified(self, "log")
        self._update_timestamp()
        trigger_event(self, "update")

    def _set_status_and_log(self, status: ControlExecutionStatus, message: str):
        self.status = status
        self._update_timestamp()
        self.add_log(message)

    def add_action_exec_history(self, action_exec_ind: int):
        self.action_exec_history.append(action_exec_ind)
        flag_modified(self, "action_exec_history")
        self._update_timestamp()

    def mark_in_progress(self, message: str = "Control: Execution started"):
        self._set_status_and_log(ControlExecutionStatus.IN_PROGRESS, message=message)

    def mark_passed(
        self, output: dict, message: str = "Execution completed successfully"
    ):
        self.output = output
        self._set_status_and_log(ControlExecutionStatus.PASSED, message=message)

    def mark_action_required(self, error: str):
        self.error_message = error
        self._set_status_and_log(
            ControlExecutionStatus.ACTION_REQUIRED, message=f"Action Required: {error}"
        )

    def mark_remediation_required(self, msg: str):
        self._set_status_and_log(
            ControlExecutionStatus.REMEDIATION_REQUIRED,
            message=f"Remediation Required: {msg}",
        )

    def mark_failed(self, error: str):
        self._set_status_and_log(
            ControlExecutionStatus.FAILED, message=f"Execution failed: {error}"
        )
        self.error_message = error

    def reset_action_exec_history(self, target_step: int):
        self.action_exec_history = self.action_exec_history[:target_step]
        flag_modified(self, "action_exec_history")
        self._update_timestamp()
