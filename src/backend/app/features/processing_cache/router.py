from fastapi import APIRouter, Depends

from app.features.processing_cache.schemas import (
    CacheInvalidationRequest,
    CacheInvalidationResponse,
    ProcessingCacheStatus,
)
from app.features.processing_cache.service import (
    get_processing_cache_status,
    invalidate_cached_json,
)
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/processing-cache", tags=["processing-cache"])


@router.get("/status", response_model=ProcessingCacheStatus)
def read_processing_cache_status(
    store: LocalStateStore = Depends(get_local_store),
) -> ProcessingCacheStatus:
    return get_processing_cache_status(store)


@router.post("/invalidate", response_model=CacheInvalidationResponse)
def invalidate_processing_cache_entry(
    payload: CacheInvalidationRequest,
    store: LocalStateStore = Depends(get_local_store),
) -> CacheInvalidationResponse:
    return invalidate_cached_json(store, payload.key)
