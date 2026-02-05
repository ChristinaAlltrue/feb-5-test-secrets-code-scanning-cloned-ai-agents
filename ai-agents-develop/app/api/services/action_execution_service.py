from uuid import UUID

from app.core.models.models import ActionExecution
from app.core.storage_dependencies.repositories.providers import RepositoryProvider


async def get_action_execution(
    provider: RepositoryProvider, action_execution_id: UUID
) -> ActionExecution:
    """
    Retrieve an action execution by ID using the repository pattern.

    Args:
        provider: Repository provider for database access
        action_execution_id: UUID of the action execution to retrieve

    Returns:
        ActionExecution: The retrieved action execution

    Raises:
        ValueError: If action execution not found
        Exception: For other database errors
    """
    # 1. Get the specific repository you need from the provider.
    action_repo = provider.get_repository(ActionExecution)

    # 2. Use the repository to perform your database operation.
    try:
        action_execution = await action_repo.get(action_execution_id)
        if action_execution is None:
            raise ValueError(f"Action execution not found: {action_execution_id}")

        return action_execution
    except Exception as e:
        raise Exception(
            f"Database error retrieving action execution {action_execution_id}"
        ) from e
