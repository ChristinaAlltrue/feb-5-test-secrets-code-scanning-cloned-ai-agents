import logfire
from fastapi import APIRouter, HTTPException

from app.api.services.command_interpreter_service import AgentPrompt, interpreter_llm

router = APIRouter(tags=["command_interpreter"])


@router.post("/command_interpreter", status_code=200, response_model=AgentPrompt)
async def command_interpreter(user_prompt: str):
    try:
        res = await interpreter_llm(user_prompt)
        return res
    except Exception as e:  # pragma: no cover
        logfire.exception("Error retrieving user command", exception=e)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving user command: {e}"
        )
