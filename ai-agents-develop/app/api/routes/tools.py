import logfire
from alltrue.agents.schema.tools import ToolsResponse
from fastapi import APIRouter, HTTPException

from app.api.services.tool_service import get_all_tools

router = APIRouter(tags=["tools"])


# TODO: add model in python api repo
@router.get("/tools", status_code=200)
def list_tools():
    try:
        return ToolsResponse(tools=get_all_tools())  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logfire.exception("Error retrieving tools", exception=e)
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {e}")
