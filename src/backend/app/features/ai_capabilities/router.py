from fastapi import APIRouter

from app.features.ai_capabilities.schemas import AiCapabilitiesResponse
from app.features.ai_capabilities.service import get_ai_capabilities

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/capabilities", response_model=AiCapabilitiesResponse)
def read_ai_capabilities() -> AiCapabilitiesResponse:
    return get_ai_capabilities()
