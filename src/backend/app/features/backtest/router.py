from fastapi import APIRouter, Depends, HTTPException

from app.features.backtest.schemas import BacktestCommand, BacktestResponse
from app.features.backtest.service import BacktestError, run_backtest
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/simulations", response_model=BacktestResponse, status_code=201)
def create_simulation(
    command: BacktestCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> BacktestResponse:
    try:
        return run_backtest(store, command)
    except BacktestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
