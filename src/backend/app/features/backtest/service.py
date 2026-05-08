from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from app.features.backtest.schemas import BacktestCommand, BacktestResponse, EquityPoint
from app.shared.datetime_utils import parse_aware_datetime
from app.shared.pydantic_compat import model_dump as _model_dump
from app.shared.state_store import LocalStateStore, State

PriceBar = Dict[str, float]
BarKey = Tuple[str, str]

PRICE_BARS: Dict[BarKey, List[Dict[str, Any]]] = {
    ("KR", "005930"): [
        {"timestamp": "2026-04-22T15:30:00+09:00", "close": 70000.0},
        {"timestamp": "2026-04-23T15:30:00+09:00", "close": 71000.0},
        {"timestamp": "2026-04-24T15:30:00+09:00", "close": 72000.0},
    ],
    ("US", "AAPL"): [
        {"timestamp": "2026-04-01T16:00:00-04:00", "close": 190.0},
        {"timestamp": "2026-04-10T16:00:00-04:00", "close": 198.5},
        {"timestamp": "2026-04-17T16:00:00-04:00", "close": 202.0},
        {"timestamp": "2026-04-22T16:00:00-04:00", "close": 210.0},
        {"timestamp": "2026-04-23T16:00:00-04:00", "close": 205.0},
        {"timestamp": "2026-04-24T16:00:00-04:00", "close": 207.15},
    ],
}


class BacktestError(ValueError):
    pass


def _parse_datetime(value: str) -> datetime:
    try:
        return parse_aware_datetime(
            value,
            error_message="timestamps must be valid ISO 8601 values",
            timezone_error_message="timestamps must include a timezone offset",
        )
    except ValueError as error:
        raise BacktestError(str(error)) from error


def _normalized_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith(".KS"):
        return normalized[:-3]
    return normalized


def _bars_for(command: BacktestCommand) -> List[Dict[str, Any]]:
    key = (command.market, _normalized_symbol(command.symbol))
    bars = PRICE_BARS.get(key)
    if not bars:
        raise BacktestError("seeded price data not found")
    return bars


def _windowed_bars(command: BacktestCommand) -> List[Dict[str, Any]]:
    entry_at = _parse_datetime(command.entry_at)
    exit_at = _parse_datetime(command.exit_at)
    if entry_at >= exit_at:
        raise BacktestError("entry_at must be before exit_at")

    bars = [
        bar
        for bar in _bars_for(command)
        if entry_at <= _parse_datetime(str(bar["timestamp"])) <= exit_at
    ]
    if len(bars) < 2:
        raise BacktestError("not enough seeded price data for the requested range")
    return bars


def _equity_curve(bars: List[Dict[str, Any]], quantity: float, entry_price: float) -> List[EquityPoint]:
    points: List[EquityPoint] = []
    for bar in bars:
        price = float(bar["close"])
        value = round(price * quantity, 2)
        points.append(
            EquityPoint(
                timestamp=str(bar["timestamp"]),
                price=price,
                value=value,
                return_pct=round((price - entry_price) / entry_price * 100, 2),
            )
        )
    return points


def _max_drawdown(points: List[EquityPoint]) -> float:
    peak = points[0].value
    max_drawdown = 0.0
    for point in points:
        peak = max(peak, point.value)
        drawdown = (point.value - peak) / peak * 100
        max_drawdown = min(max_drawdown, drawdown)
    return round(max_drawdown, 2)


def run_backtest(store: LocalStateStore, command: BacktestCommand) -> BacktestResponse:
    bars = _windowed_bars(command)
    entry_price = float(bars[0]["close"])
    exit_price = float(bars[-1]["close"])
    quantity = float(command.quantity)
    equity_curve = _equity_curve(bars, quantity, entry_price)

    response = BacktestResponse(
        simulation_id=f"backtest_{uuid4().hex}",
        analysis_request_id=command.analysis_request_id,
        evaluation_kind="pnl_simulation",
        market=command.market,
        symbol=_normalized_symbol(command.symbol),
        entry_at=command.entry_at,
        exit_at=command.exit_at,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        gross_return_pct=round((exit_price - entry_price) / entry_price * 100, 2),
        gross_pnl=round((exit_price - entry_price) * quantity, 2),
        max_drawdown_pct=_max_drawdown(equity_curve),
        equity_curve=equity_curve,
        source="seeded_local_fixture",
    )

    def mutate(state: State) -> BacktestResponse:
        state["backtests"][response.simulation_id] = _model_dump(response)
        return response

    return store.update(mutate)
