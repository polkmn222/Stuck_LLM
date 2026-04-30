from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _clear_provider_environment(monkeypatch) -> None:
    for name in [
        "OPENAI_API_KEY",
        "OpenAI_API_Key",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "CEREBRAS_API_KEY",
        "CEREBRAS_MODEL",
        "CEREBRAS_BASE_URL",
        "SERPAPI_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_korean_if_bought_date_returns_separate_pnl_simulation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "애플을 4월 1일에 샀다면 지금 수익률은?",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pnl_simulation"
    assert body["analysis_result"] is None
    assert body["analysis_request"] is None
    assert body["market_snapshot"]["symbol"] == "AAPL"
    assert body["backtest_result"]["entry_at"] == "2026-04-01T16:00:00-04:00"
    assert body["backtest_result"]["exit_at"] == "2026-04-24T16:00:00-04:00"
    assert body["backtest_result"]["entry_price"] == 190.0
    assert body["backtest_result"]["exit_price"] == 207.15
    assert body["backtest_result"]["gross_return_pct"] == 9.03
    assert body["messages"][-1]["backtest_result"]["gross_return_pct"] == 9.03
    assert "별도 PnL 시뮬레이션" in body["messages"][-1]["content"]
    assert "미래 가격을 섞지 않습니다" in body["messages"][-1]["content"]
