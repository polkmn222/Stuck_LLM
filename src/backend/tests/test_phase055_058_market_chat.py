from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import LiveAnalysisOutput, LiveProviderRequest
from app.features.market_data import service as market_data_service
from app.main import create_app


class FollowUpIntentProvider:
    def __init__(self, question: str) -> None:
        self.question = question
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return {
            "intent": "follow_up",
            "stock_query": None,
            "market": None,
            "horizon_type": None,
            "analysis_mode": None,
            "source_hints": [],
            "needs_follow_up": True,
            "follow_up_question": self.question,
        }

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        raise AssertionError("Ambiguous follow-up prompts should not run analysis.")


def _save_openai_credential(client: TestClient, raw_key: str) -> None:
    response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": raw_key,
        },
    )
    assert response.status_code == 200


def _serpapi_quote_payload(
    *,
    title: str,
    stock: str,
    price: float,
    date: str = "Apr 28 2026, 04:00:00 PM UTC-04:00",
    graph: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "search_metadata": {"status": "Success"},
        "summary": {
            "title": title,
            "stock": stock,
            "exchange": "NASDAQ",
            "extracted_price": price,
            "currency": "USD",
            "price_movement": {
                "percentage": 1.18,
                "value": 3.15,
                "movement": "Up",
            },
            "date": date,
        },
        "graph": graph
        if graph is not None
        else [
            {
                "price": price - 3.15,
                "currency": "USD",
                "date": "Apr 28 2026, 09:30 AM UTC-04:00",
                "volume": 1000,
            },
            {
                "price": price,
                "currency": "USD",
                "date": date,
                "volume": 2000,
            },
        ],
    }


def test_plain_apple_lookup_returns_snapshot_without_horizon_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase055-secret")
    monkeypatch.setenv("STUCK_LLM_USD_KRW_RATE", "1380")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "AAPL:NASDAQ"
        assert api_key == "serpapi-phase055-secret"
        return _serpapi_quote_payload(title="Apple Inc", stock="AAPL", price=270.71)

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(
        create_app(state_path=tmp_path / "state.json"),
        raise_server_exceptions=False,
    )

    response = client.post(
        "/conversations",
        json={
            "content": "apple",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "market_snapshot"
    assert body["missing_inputs"] == []
    assert body["market_snapshot"]["market"] == "US"
    assert body["market_snapshot"]["symbol"] == "AAPL"
    assert body["market_snapshot"]["currency"] == "USD"
    assert body["messages"][-1]["market_snapshot"]["symbol"] == "AAPL"
    assert "horizon" not in body["messages"][-1]["content"].lower()
    assert "serpapi-phase055-secret" not in response.text


def test_korean_google_price_query_routes_to_us_quote_and_converts_chat_price(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase057-secret")
    monkeypatch.setenv("STUCK_LLM_USD_KRW_RATE", "1380")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "GOOG:NASDAQ"
        assert api_key == "serpapi-phase057-secret"
        return _serpapi_quote_payload(title="Alphabet Inc Class C", stock="GOOG", price=348.0)

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "구글 주가",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "market_snapshot"
    assert body["market_snapshot"]["market"] == "US"
    assert body["market_snapshot"]["symbol"] == "GOOG"
    assert body["market_snapshot"]["currency"] == "USD"
    assert "348.00 USD" in body["messages"][-1]["content"]
    assert "480,240 KRW" in body["messages"][-1]["content"]


def test_korean_us_snapshot_uses_serpapi_usd_krw_rate_when_env_rate_is_absent(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase063-secret")
    monkeypatch.delenv("STUCK_LLM_USD_KRW_RATE", raising=False)

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert api_key == "serpapi-phase063-secret"
        if query == "GOOG:NASDAQ":
            return _serpapi_quote_payload(
                title="Alphabet Inc Class C",
                stock="GOOG",
                price=348.0,
            )
        if query == "USD-KRW":
            return _serpapi_quote_payload(
                title="USD / KRW",
                stock="USD-KRW",
                price=1392.5,
            )
        raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "구글 주가",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    content = response.json()["messages"][-1]["content"]
    assert "348.00 USD" in content
    assert "484,590 KRW" in content
    assert "USD/KRW 1,392.50 기준" in content


def test_llm_follow_up_question_is_used_for_ambiguous_stock_request(
    tmp_path: Path,
) -> None:
    raw_key = "sk-phase055-follow-up-secret"
    question = "어떤 은행 종목을 볼까요? 회사명이나 티커를 하나만 알려주세요."
    provider = FollowUpIntentProvider(question)
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "은행주 좀 봐줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["stock"]
    assert body["messages"][-1]["content"] == question
    assert body["messages"][-1]["meta"] == "확인 필요"
    assert provider.analysis_requests == []
    assert raw_key not in response.text


def test_us_quote_skips_serpapi_candidate_without_graph_for_windowed_chart(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase056-secret")
    attempted_queries = []

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        attempted_queries.append(query)
        assert api_key == "serpapi-phase056-secret"
        assert window == "5D"
        if query == "AAPL:NASDAQ":
            return _serpapi_quote_payload(
                title="Apple Inc",
                stock="AAPL",
                price=270.71,
                graph=[],
            )
        if query == "NASDAQ:AAPL":
            return _serpapi_quote_payload(
                title="Apple Inc",
                stock="AAPL",
                price=270.71,
                graph=[
                    {
                        "price": 267.56,
                        "currency": "USD",
                        "date": "Apr 23 2026, 04:00 PM UTC-04:00",
                        "volume": 100,
                    },
                    {
                        "price": 270.71,
                        "currency": "USD",
                        "date": "Apr 28 2026, 04:00 PM UTC-04:00",
                        "volume": 200,
                    },
                ],
            )
        raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/AAPL?window=5D")

    assert response.status_code == 200
    body = response.json()
    assert attempted_queries == ["AAPL:NASDAQ", "NASDAQ:AAPL"]
    assert body["chart_window"] == "5D"
    assert body["chart_bars"][0]["close"] == 267.56
    assert body["chart_bars"][-1]["close"] == 270.71


def test_sp500_symbol_query_routes_to_us_quote_when_default_market_is_kr(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase062-secret")
    monkeypatch.setenv("STUCK_LLM_USD_KRW_RATE", "1390")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "WMT:NYSE"
        assert api_key == "serpapi-phase062-secret"
        return _serpapi_quote_payload(
            title="Walmart Inc",
            stock="WMT",
            price=143.21,
            date="Apr 29 2026, 04:38:40 AM UTC-04:00",
        )

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "월마트 주가",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "market_snapshot"
    assert body["market_snapshot"]["market"] == "US"
    assert body["market_snapshot"]["symbol"] == "WMT"
    assert body["market_snapshot"]["currency"] == "USD"
    assert "143.21 USD" in body["messages"][-1]["content"]
    assert "serpapi-phase062-secret" not in response.text
