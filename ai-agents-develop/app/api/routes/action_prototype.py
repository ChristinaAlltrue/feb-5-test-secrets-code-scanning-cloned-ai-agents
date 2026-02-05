import logfire
from alltrue.agents.schema.action_prototype import GetAllActionsResponse
from fastapi import APIRouter, HTTPException

from app.api.services.action_prototype_service import (
    get_all_action_prototypes as service_get_all_action_prototypes,
)

router = APIRouter(tags=["action_prototype"])


@router.get("/action-prototypes", status_code=200)
def get_all_actions_prototypes():
    try:
        res = service_get_all_action_prototypes()
        return GetAllActionsResponse(actions=res)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logfire.exception("Error retrieving action prototypes", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving action prototypes: {e}"
        )
