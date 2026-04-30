from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.features.settings.schemas import DefaultMarket

MarketChartWindow = Literal["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"]


class MarketBar(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketKeyStat(BaseModel):
    label: str
    value: str


class MarketNewsItem(BaseModel):
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None
    snippet: Optional[str] = None


class MarketQuote(BaseModel):
    market: DefaultMarket
    symbol: str
    name: str
    exchange: str
    currency: str
    last_price: float
    previous_close: Optional[float] = None
    change_pct: Optional[float] = None
    as_of_at: str
    source: str
    chart_window: MarketChartWindow = "1D"
    chart_bars: List[MarketBar] = Field(default_factory=list)
    key_stats: List[MarketKeyStat] = Field(default_factory=list)
    news_items: List[MarketNewsItem] = Field(default_factory=list)
