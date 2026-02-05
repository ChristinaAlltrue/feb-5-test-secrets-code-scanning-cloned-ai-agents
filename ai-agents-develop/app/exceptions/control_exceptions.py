class ControlNotFoundException(Exception):
    """Exception raised when a control is not found."""


class ControlExecutionNotFoundException(Exception):
    """Exception raised when a control execution is not found."""


class ControlEntityNotFoundException(Exception):
    """Exception raised when a control entity is not found."""


# ===========Graph Execution Exceptions===========


class GraphExecutionActionRequiredException(Exception):
    """Exception raised when a graph execution action is required."""


class GraphExecutionRemediationRequiredException(Exception):
    """Exception raised when a graph execution remediation is required."""


class GraphExecutionFailedException(Exception):
    """Exception raised when a graph execution failed."""


class PauseExecution(Exception):
    """Raised to indicate the agent should pause execution."""

    def __init__(self, data: dict | None = None):
        self.data = data or {}
        super().__init__(f"Execution paused: {self.data}")
