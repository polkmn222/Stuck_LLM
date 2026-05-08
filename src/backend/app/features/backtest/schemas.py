from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.settings.schemas import DefaultMarket
from app.shared.validation import require_timezone_datetime


class BacktestCommand(BaseModel):
    analysis_request_id: Optional[str] = None
    market: DefaultMarket
    symbol: str = Field(min_length=1, max_length=32)
    entry_at: str
    exit_at: str
    quantity: float = Field(gt=0)

    @field_validator("entry_at", "exit_at")
    @classmethod
    def require_aware_timestamp(cls, value: str) -> str:
        return require_timezone_datetime(value)


class EquityPoint(BaseModel):
    timestamp: str
    price: float
    value: float
    return_pct: float


class BacktestResponse(BaseModel):
    simulation_id: str
    analysis_request_id: Optional[str]
    evaluation_kind: Literal["pnl_simulation"] = "pnl_simulation"
    market: DefaultMarket
    symbol: str
    entry_at: str
    exit_at: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_return_pct: float
    gross_pnl: float
    max_drawdown_pct: float
    equity_curve: List[EquityPoint]
    source: str
