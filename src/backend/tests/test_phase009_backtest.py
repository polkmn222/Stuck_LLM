from fastapi.testclient import TestClient

from app.main import create_app


def test_backtest_simulation_calculates_pnl_and_equity_curve(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/backtests/simulations",
        json={
            "analysis_request_id": "analysis_005930",
            "market": "KR",
            "symbol": "005930",
            "entry_at": "2026-04-22T15:30:00+09:00",
            "exit_at": "2026-04-24T15:30:00+09:00",
            "quantity": 10,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["market"] == "KR"
    assert body["symbol"] == "005930"
    assert body["entry_price"] == 70000.0
    assert body["exit_price"] == 72000.0
    assert body["quantity"] == 10.0
    assert body["gross_return_pct"] == 2.86
    assert body["gross_pnl"] == 20000.0
    assert body["max_drawdown_pct"] == 0.0
    assert body["source"] == "seeded_local_fixture"
    assert body["equity_curve"] == [
        {
            "timestamp": "2026-04-22T15:30:00+09:00",
            "price": 70000.0,
            "value": 700000.0,
            "return_pct": 0.0,
        },
        {
            "timestamp": "2026-04-23T15:30:00+09:00",
            "price": 71000.0,
            "value": 710000.0,
            "return_pct": 1.43,
        },
        {
            "timestamp": "2026-04-24T15:30:00+09:00",
            "price": 72000.0,
            "value": 720000.0,
            "return_pct": 2.86,
        },
    ]


def test_backtest_reports_drawdown_for_declining_path(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/backtests/simulations",
        json={
            "market": "US",
            "symbol": "AAPL",
            "entry_at": "2026-04-22T16:00:00-04:00",
            "exit_at": "2026-04-24T16:00:00-04:00",
            "quantity": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["entry_price"] == 210.0
    assert body["exit_price"] == 207.15
    assert body["gross_return_pct"] == -1.36
    assert body["gross_pnl"] == -14.25
    assert body["max_drawdown_pct"] == -2.38


def test_backtest_rejects_invalid_date_range(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/backtests/simulations",
        json={
            "market": "KR",
            "symbol": "005930",
            "entry_at": "2026-04-24T15:30:00+09:00",
            "exit_at": "2026-04-22T15:30:00+09:00",
            "quantity": 10,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "entry_at must be before exit_at"
