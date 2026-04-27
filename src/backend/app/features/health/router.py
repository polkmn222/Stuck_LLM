from fastapi import APIRouter

from app.features.health.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(service="stock-analysis-agent-api", status="ok")
