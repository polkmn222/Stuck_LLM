from fastapi import APIRouter, Depends

from app.features.ingestion.schemas import SourceCollectionCommand, SourceCollectionResponse
from app.features.ingestion.service import collect_sources
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/collect", response_model=SourceCollectionResponse, status_code=201)
def collect_sources_endpoint(
    command: SourceCollectionCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> SourceCollectionResponse:
    return collect_sources(store, command)
