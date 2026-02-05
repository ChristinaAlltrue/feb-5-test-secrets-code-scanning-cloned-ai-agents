from uuid import UUID

import logfire
from alltrue.agents.schema.action_execution import ActionExecutionResponse
from fastapi import APIRouter, Depends

from app.api.services.action_execution_service import get_action_execution
from app.core.storage_dependencies.repositories.providers import RepositoryProvider
from app.core.storage_dependencies.storage_dependencies import get_provider_dependency

router = APIRouter(tags=["action_execution"])


@router.get(
    "/action-executions/{action_execution_id}", response_model=ActionExecutionResponse
)
async def get_action_execution_endpoint(
    action_execution_id: UUID,
    provider: RepositoryProvider = Depends(get_provider_dependency),
):
    """
    Get an action execution status by its ID.
    """

    logfire.debug(f"Retrieving action execution: {action_execution_id}")

    try:
        result = await get_action_execution(provider, action_execution_id)
        logfire.info(f"Retrieved action execution: {action_execution_id}")
        return result
    except Exception as e:
        logfire.error(f"Failed to retrieve action execution {action_execution_id}: {e}")
        raise
