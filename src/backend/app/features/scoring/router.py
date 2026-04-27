from fastapi import APIRouter, Depends

from app.features.scoring.schemas import ScoreCommand, ScoreResponse
from app.features.scoring.service import score_evidence
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/evaluate", response_model=ScoreResponse, status_code=201)
def evaluate_score(
    command: ScoreCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> ScoreResponse:
    return score_evidence(store, command)
