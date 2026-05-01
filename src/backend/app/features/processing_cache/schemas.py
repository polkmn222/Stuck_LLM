from typing import Dict

from pydantic import BaseModel, Field


class CacheBucketStatus(BaseModel):
    total_entries: int = Field(ge=0)
    expired_entries: int = Field(ge=0)
    namespaces: Dict[str, int] = Field(default_factory=dict)


class ProcessingCacheStatus(BaseModel):
    kv_cache: CacheBucketStatus
    news_processing_runs: int = Field(ge=0)
    prediction_artifacts: int = Field(ge=0)


class CacheInvalidationRequest(BaseModel):
    key: str = Field(min_length=1, max_length=256)


class CacheInvalidationResponse(BaseModel):
    key: str
    removed: bool
