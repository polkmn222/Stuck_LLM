from fastapi import APIRouter, Depends

from app.features.analysis.schemas import AnalysisRequestCommand, AnalysisResponse
from app.features.analysis.service import create_analysis
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/requests", response_model=AnalysisResponse, status_code=201)
def create_analysis_endpoint(
    command: AnalysisRequestCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> AnalysisResponse:
    return create_analysis(store, command)
