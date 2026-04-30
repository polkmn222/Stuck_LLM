from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.settings.schemas import AnalysisMode, DefaultMarket
from app.shared.validation import require_timezone_datetime

SourceAdapter = Literal[
    "reddit",
    "us_news",
    "polling_sentiment",
    "global_macro",
    "naver_news",
    "tavily_news",
    "gnews_news",
    "serpapi_google_news",
]
CollectionStatus = Literal["completed"]


class SourceCollectionCommand(BaseModel):
    market: DefaultMarket
    symbol: str = Field(min_length=1, max_length=32)
    stock_name: str = Field(min_length=1, max_length=160)
    as_of_at: str
    analysis_mode: AnalysisMode
    source_adapters: List[SourceAdapter] = Field(min_length=1, max_length=8)

    @field_validator("as_of_at")
    @classmethod
    def require_aware_as_of_at(cls, value: str) -> str:
        return require_timezone_datetime(value)


class CollectedSourceDocument(BaseModel):
    id: str
    source_type: SourceAdapter
    source_name: str
    url: str
    title: str
    author: Optional[str] = None
    published_at: str
    fetched_at: str
    content_text: str
    language: str
    adapter: SourceAdapter
    relevance_score: float
    safety_flags: List[str]


class SourceCollectionResponse(BaseModel):
    collection_id: str
    status: CollectionStatus
    market: DefaultMarket
    symbol: str
    stock_name: str
    as_of_at: str
    analysis_mode: AnalysisMode
    adapters_run: List[SourceAdapter]
    document_count: int
    documents: List[CollectedSourceDocument]
    warnings: List[str]
