from alltrue.agents.schema.predefined import Frameworks
from fastapi import APIRouter

from app.api.services.framework_service import load_all_predefined_frameworks

router = APIRouter(tags=["predefined-framework"])


@router.get(
    "/predefined-frameworks",
    response_model=Frameworks,
    status_code=200,
    description="Get all predefined frameworks",
)
def get_predefined_frameworks():
    return Frameworks(frameworks=load_all_predefined_frameworks())
