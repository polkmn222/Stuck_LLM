from pydantic import BaseModel

from app.features.settings.schemas import DefaultMarket


class MarketQuote(BaseModel):
    market: DefaultMarket
    symbol: str
    name: str
    exchange: str
    currency: str
    last_price: float
    as_of_at: str
    source: str
