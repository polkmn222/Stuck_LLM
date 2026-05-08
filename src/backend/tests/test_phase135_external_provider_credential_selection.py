import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import ChatCompletionProviderRequest
from app.features.market_data import service as market_data_service
from app.features.market_data.schemas import MarketQuote
from app.main import create_app


class NewsIntentProvider:
    def __init__(self) -> None:
        self.completion_requests: List[ChatCompletionProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        return {
            "intent": "news_digest",
            "stock_query": "AAPL",
            "market": "US",
            "horizon_type": None,
            "analysis_mode": None,
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def complete_chat(self, request: ChatCompletionProviderRequest) -> str:
        self.completion_requests.append(request)
        return "Selected-key news summary."

    def analyze(self, request: Any) -> Any:
        raise AssertionError("News digest should not run stock analysis.")


def _apple_quote() -> MarketQuote:
    return MarketQuote(
        market="US",
        symbol="AAPL",
        name="Apple Inc",
        exchange="NASDAQ",
        currency="USD",
        last_price=270.71,
        previous_close=267.56,
        change_pct=1.18,
        as_of_at="2026-05-06T16:00:00-04:00",
        source="serpapi_google_finance",
    )


def _save_llm_credential(client: TestClient) -> None:
    response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-phase135-llm-secret",
        },
    )
    assert response.status_code == 200


def test_external_provider_credentials_are_encrypted_masked_and_selectable(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    client = TestClient(create_app(state_path=state_path))

    save_response = client.post(
        "/credentials/external/profiles",
        json={
            "credential_id": "tavily_news_key",
            "label": "Tavily selected",
            "provider": "tavily",
            "api_key": "tvly-phase135-selected-secret",
            "make_active": True,
        },
    )
    list_response = client.get("/credentials/external/profiles")

    assert save_response.status_code == 200
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["active_credential_ids"]["tavily"] == "tavily_news_key"
    assert body["credentials"][0]["api_key_mask"] == "tvly...cret"
    assert body["credentials"][0]["provider"] == "tavily"
    assert "tvly-phase135-selected-secret" not in list_response.text
    assert "tvly-phase135-selected-secret" not in state_path.read_text()
    assert "encrypted_api_key" in state_path.read_text()


def test_conversation_news_uses_selected_external_key_over_environment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.features.news_digest import service as news_digest_service

    selected_key = "tvly-phase135-selected-secret"
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-phase135-env-secret")
    monkeypatch.delenv("GNEWS_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.delenv("EVENTREGISTRY_API_KEY", raising=False)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": _apple_quote() if symbol == "AAPL" else None,
        raising=False,
    )

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        _ = headers, timeout_seconds
        assert url == "https://api.tavily.com/search"
        assert payload is not None
        assert payload["api_key"] == selected_key
        return {
            "results": [
                {
                    "title": "Apple selected-key headline",
                    "url": "https://example.com/apple-selected-key",
                    "content": "Selected Tavily key returned this Apple headline.",
                    "published_date": "2026-05-06T12:00:00-04:00",
                }
            ]
        }

    def unexpected_fetch_text(*args, **kwargs) -> str:
        raise AssertionError("Selected Tavily credential should avoid free RSS fallback.")

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(news_digest_service, "_fetch_text", unexpected_fetch_text, raising=False)

    provider = NewsIntentProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_llm_credential(client)
    external_response = client.post(
        "/credentials/external/profiles",
        json={
            "credential_id": "tavily_selected",
            "label": "Selected Tavily",
            "provider": "tavily",
            "api_key": selected_key,
            "make_active": True,
        },
    )
    assert external_response.status_code == 200

    response = client.post(
        "/conversations",
        json={
            "content": "애플 뉴스 가져와줘",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "news_digest"
    assert body["news_digest"]["provider_runs"][0]["provider"] == "tavily_news"
    assert body["news_digest"]["important_articles"][0]["title"] == "Apple selected-key headline"
    serialized = json.dumps(body)
    assert selected_key not in serialized
    assert "tvly-phase135-env-secret" not in serialized
