import logfire
from alltrue.agents.schema.llm_models import LLMModelsResponse
from fastapi import APIRouter, HTTPException

from app.api.services.model_service import get_all_models

router = APIRouter(tags=["llm-models"])


@router.get("/llm-models", status_code=200)
def list_models():
    try:
        return LLMModelsResponse(models=get_all_models())  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logfire.exception("Error retrieving models", exception=e)
        raise HTTPException(status_code=500, detail=f"Error retrieving models: {e}")
