from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import LiveAnalysisOutput, LiveProviderRequest
from app.features.market_data import service as market_data_service
from app.main import create_app


class SimpleChatProvider:
    def __init__(self) -> None:
        self.intent_requests: List[Any] = []
        self.chat_requests: List[Any] = []
        self.analysis_requests: List[Any] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return {
            "intent": "other",
            "stock_query": None,
            "market": None,
            "horizon_type": None,
            "analysis_mode": None,
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def complete_chat(self, request: Any) -> str:
        self.chat_requests.append(request)
        if len(self.chat_requests) == 1:
            return "안녕하세요. 저장된 API key로 대화 중입니다."
        return "이전 대화를 이어서 답변할 수 있습니다."

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        raise AssertionError("Generic chat should not run stock analysis.")


def _save_cerebras_credential(client: TestClient, raw_key: str) -> None:
    response = client.put(
        "/credentials/llm",
        json={
            "provider": "cerebras",
            "model": "llama3.1-8b",
            "base_url": None,
            "api_key": raw_key,
        },
    )
    assert response.status_code == 200


def _serpapi_aapl_payload() -> Dict[str, Any]:
    return {
        "search_metadata": {"status": "Success"},
        "summary": {
            "title": "Apple Inc",
            "stock": "AAPL",
            "exchange": "NASDAQ",
            "extracted_price": 207.15,
            "currency": "USD",
            "price_movement": {
                "percentage": 1.25,
                "value": 2.56,
                "movement": "Up",
            },
            "date": "Apr 28 2026, 04:00:00 PM UTC-04:00",
        },
        "knowledge_graph": {
            "key_stats": {
                "stats": [
                    {"label": "Previous close", "value": "$204.59"},
                    {"label": "Market cap", "value": "$3.12T"},
                    {"label": "P/E ratio", "value": "31.4"},
                ]
            }
        },
        "news_results": [
            {
                "title": "Apple supplier checks improve",
                "link": "https://example.com/apple-suppliers",
                "source": "Market Wire",
                "date": "Apr 28 2026, 01:15 PM UTC-04:00",
                "snippet": "Supplier checks pointed to stronger iPhone demand.",
            }
        ],
        "graph": [
            {
                "price": 204.59,
                "currency": "USD",
                "date": "Apr 28 2026, 09:30 AM UTC-04:00",
                "volume": 1000,
            },
            {
                "price": 207.15,
                "currency": "USD",
                "date": "Apr 28 2026, 04:00 PM UTC-04:00",
                "volume": 2000,
            },
        ],
    }


def test_saved_llm_key_supports_persistent_simple_chat(tmp_path: Path) -> None:
    raw_key = "csk-phase038-simple-chat-secret"
    provider = SimpleChatProvider()
    client = TestClient(
        create_app(
            state_path=tmp_path / "state.json",
            llm_analysis_provider=provider,
        )
    )
    _save_cerebras_credential(client, raw_key)

    first_response = client.post(
        "/conversations",
        json={
            "content": "안녕, 간단히 대화 가능해?",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert first_response.status_code == 201
    assert raw_key not in first_response.text
    first_body = first_response.json()
    assert first_body["status"] == "chat_completed"
    assert first_body["messages"][-1]["content"] == "안녕하세요. 저장된 API key로 대화 중입니다."
    assert first_body["analysis_request"] is None
    assert first_body["analysis_result"] is None
    assert provider.chat_requests
    assert provider.analysis_requests == []

    second_response = client.post(
        f"/conversations/{first_body['conversation_id']}/messages",
        json={
            "content": "방금 뭐라고 했어?",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert second_response.status_code == 200
    second_body = second_response.json()
    assert second_body["status"] == "chat_completed"
    assert second_body["messages"][-1]["content"] == "이전 대화를 이어서 답변할 수 있습니다."
    assert len(second_body["messages"]) == 4
    assert any(
        message["content"] == "안녕하세요. 저장된 API key로 대화 중입니다."
        for message in provider.chat_requests[1].messages
    )

    list_response = client.get("/conversations")

    assert list_response.status_code == 200
    summaries = list_response.json()["conversations"]
    assert summaries[0]["conversation_id"] == first_body["conversation_id"]
    assert summaries[0]["title"] == "안녕, 간단히 대화 가능해?"
    assert summaries[0]["status"] == "chat_completed"


def test_ticker_only_request_returns_rich_snapshot_without_horizon_prompt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase038-secret")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "AAPL:NASDAQ"
        assert api_key == "serpapi-phase038-secret"
        return _serpapi_aapl_payload()

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
            "content": "AAPL",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert response.status_code == 201
    assert "serpapi-phase038-secret" not in response.text
    body = response.json()
    assert body["status"] == "market_snapshot"
    assert body["missing_inputs"] == []
    assert body["analysis_request"] is None
    assert body["market_snapshot"]["symbol"] == "AAPL"
    assert body["market_snapshot"]["source"] == "serpapi_google_finance"
    assert body["market_snapshot"]["chart_bars"][1]["close"] == 207.15
    assert body["market_snapshot"]["key_stats"] == [
        {"label": "Market cap", "value": "$3.12T"},
        {"label": "P/E ratio", "value": "31.4"},
    ]
    assert body["market_snapshot"]["news_items"] == [
        {
            "title": "Apple supplier checks improve",
            "url": "https://example.com/apple-suppliers",
            "source": "Market Wire",
            "published_at": "2026-04-28T13:15:00-04:00",
            "snippet": "Supplier checks pointed to stronger iPhone demand.",
        }
    ]
    assert body["messages"][-1]["market_snapshot"]["symbol"] == "AAPL"
    assert "horizon" not in body["messages"][-1]["content"].lower()

    persisted = client.get(f"/conversations/{body['conversation_id']}")

    assert persisted.status_code == 200
    assert persisted.json()["messages"][-1]["market_snapshot"]["news_items"][0]["title"] == (
        "Apple supplier checks improve"
    )


def test_ticker_snapshot_flattens_nested_google_finance_news_items(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase047-secret")
    payload = _serpapi_aapl_payload()
    payload["news_results"] = [
        {
            "title": "In the news",
            "items": [
                {
                    "snippet": "Apple services revenue reaches a new high",
                    "link": "https://example.com/apple-services",
                    "source": "Finance Desk",
                    "date": "Apr 28 2026, 02:45 PM UTC-04:00",
                    "thumbnail": "https://example.com/apple-services.jpg",
                }
            ],
        }
    ]

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "AAPL:NASDAQ"
        assert api_key == "serpapi-phase047-secret"
        return payload

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
            "content": "AAPL",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "market_snapshot"
    assert body["market_snapshot"]["news_items"] == [
        {
            "title": "Apple services revenue reaches a new high",
            "url": "https://example.com/apple-services",
            "source": "Finance Desk",
            "published_at": "2026-04-28T14:45:00-04:00",
            "snippet": "Apple services revenue reaches a new high",
        }
    ]
    assert "serpapi-phase047-secret" not in response.text
