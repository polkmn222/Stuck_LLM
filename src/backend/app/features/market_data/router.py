from fastapi import APIRouter, HTTPException

from app.features.market_data.schemas import MarketQuote
from app.features.market_data.service import get_quote

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/quotes/{market}/{symbol}", response_model=MarketQuote)
def read_quote(market: str, symbol: str) -> MarketQuote:
    quote = get_quote(market, symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail="Market quote not found")
    return quote
