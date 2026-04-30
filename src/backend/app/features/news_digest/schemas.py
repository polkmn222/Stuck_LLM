from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.features.settings.schemas import DefaultMarket

NewsProvider = Literal[
    "tavily_news",
    "naver_news",
    "gnews_news",
    "serpapi_google_news",
    "serpapi_google_web",
    "serpapi_social_web",
]
NewsSearchStatus = Literal["completed", "partial", "empty"]
NewsProviderRunStatus = Literal["completed", "missing_credential", "provider_error"]
NewsCategory = Literal[
    "official",
    "earnings",
    "core_business",
    "controversy",
    "market_reaction",
    "product_service",
    "quote_page",
    "other",
]


class NewsSearchRun(BaseModel):
    provider: NewsProvider
    query: str
    result_count: int = Field(ge=0)
    status: NewsProviderRunStatus
    warning: Optional[str] = None


class NewsArticle(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    provider: NewsProvider
    query: str
    rank: int
    category: NewsCategory = "other"
    headline_ko: Optional[str] = None
    summary_ko: Optional[str] = None
    importance_score: float = 0.0
    source_domain: Optional[str] = None


class NewsDigest(BaseModel):
    digest_id: str
    status: NewsSearchStatus
    market: DefaultMarket
    symbol: str
    stock_name: str
    query: str
    generated_at: str
    summary: str
    key_points: List[str]
    important_articles: List[NewsArticle]
    additional_articles: List[NewsArticle]
    provider_runs: List[NewsSearchRun]
    warnings: List[str]
