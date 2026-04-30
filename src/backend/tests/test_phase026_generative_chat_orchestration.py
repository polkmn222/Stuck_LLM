import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatIntentProviderRequest,
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
    LlmProviderConfig,
    OpenAiCompatibleAnalysisProvider,
)
from app.features.market_data import service as market_data_service
from app.main import create_app


class IntentAndAnalysisProvider:
    def __init__(self, intent: Dict[str, Any]) -> None:
        self.intent = intent
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return self.intent

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="LLM-orchestrated Samsung analysis.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Selected source supports memory demand",
                    quote_excerpt="Memory demand and macro conditions support the setup.",
                )
            ],
        )


class QueuedIntentProvider:
    def __init__(self, intents: List[Dict[str, Any]]) -> None:
        self.intents = intents
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        if not self.intents:
            raise AssertionError("No queued intent was available.")
        return self.intents.pop(0)

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        raise AssertionError("Market snapshot confirmation should not run stock analysis.")


def _clear_provider_environment(monkeypatch) -> None:
    for name in [
        "OPENAI_API_KEY",
        "OpenAI_API_Key",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "CEREBRAS_API_KEY",
        "CEREBRAS_MODEL",
        "CEREBRAS_BASE_URL",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


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


def test_chat_uses_structured_intent_for_non_literal_stock_and_source_hints(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    raw_key = "sk-phase026-orchestration-secret"
    provider = IntentAndAnalysisProvider(
        {
            "intent": "stock_analysis",
            "stock_query": "Samsung Electronics",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "deep",
            "source_hints": ["reddit", "global macro"],
            "needs_follow_up": False,
            "follow_up_question": None,
        }
    )
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": (
                "Give me a medium-term deep view on the Korean memory leader. "
                "Use Reddit sentiment and macro sources."
            ),
            "market": "KR",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert body["analysis_request"] == {
        "market": "KR",
        "symbol": "005930",
        "stock_name": "Samsung Electronics",
        "horizon_type": "swing",
        "analysis_mode": "deep",
    }
    assert body["analysis_result"]["source_audit"]["included_by_source_type"] == {
        "reddit": 2,
        "global_macro": 2,
        "market_data": 1,
    }
    assert body["analysis_result"]["source_audit"]["source_warnings"] == [
        "seeded_offline_adapters_only"
    ]
    assert provider.intent_requests
    assert provider.analysis_requests
    intent_prompt = json.dumps(provider.intent_requests[0].messages)
    assert "Korean memory leader" in intent_prompt
    assert raw_key not in intent_prompt


def test_llm_intent_cannot_bypass_unresolved_stock_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    provider = IntentAndAnalysisProvider(
        {
            "intent": "stock_analysis",
            "stock_query": "Unlisted Moonshot Holdings",
            "market": "US",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }
    )
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, "sk-phase026-validation-secret")

    response = client.post(
        "/conversations",
        json={"content": "Analyze the company we discussed for a swing trade."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["stock"]
    assert body["analysis_request"] is None
    assert provider.intent_requests
    assert provider.analysis_requests == []


def test_llm_intent_cannot_bypass_existing_typo_confirmation_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    provider = IntentAndAnalysisProvider(
        {
            "intent": "stock_analysis",
            "stock_query": "Samsung Electronics",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }
    )
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, "sk-phase026-confirmation-secret")

    response = client.post(
        "/conversations",
        json={"content": "삼성전가 스윙 분석해줘", "market": "KR"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["stock_confirmation"]
    assert body["analysis_request"] is None
    assert provider.intent_requests
    assert provider.analysis_requests == []


def test_openai_compatible_provider_sends_structured_chat_intent_payload() -> None:
    calls: List[Dict[str, Any]] = []
    raw_key = "sk-phase026-provider-secret"

    def http_post(url, headers, payload, timeout_seconds):
        calls.append(
            {
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
                "url": url,
            }
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "intent": "stock_analysis",
                                "stock_query": "Samsung Electronics",
                                "market": "KR",
                                "horizon_type": "swing",
                                "analysis_mode": "quick",
                                "source_hints": ["reddit"],
                                "needs_follow_up": False,
                                "follow_up_question": None,
                            }
                        )
                    }
                }
            ]
        }

    provider = OpenAiCompatibleAnalysisProvider(
        http_post=http_post,
        max_retries=0,
    )

    output = provider.interpret_chat(
        ChatIntentProviderRequest(
            config=LlmProviderConfig(
                provider="openai",
                model="gpt-4.1-mini",
                base_url="https://api.openai.com/v1",
                api_key=raw_key,
            ),
            messages=[{"role": "user", "content": "Return structured intent."}],
            language="en",
        )
    )

    assert output.stock_query == "Samsung Electronics"
    assert calls[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {raw_key}"
    assert calls[0]["payload"]["response_format"]["json_schema"]["name"] == (
        "stock_chat_intent"
    )
    assert calls[0]["payload"]["temperature"] == 0
    assert raw_key not in json.dumps(calls[0]["payload"])


def test_korean_apple_alias_returns_us_snapshot_without_confirmation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    raw_llm_key = "sk-phase053-intent-secret"
    raw_serpapi_key = "serpapi-phase053-secret"
    monkeypatch.setenv("SERPAPI_API_KEY", raw_serpapi_key)
    monkeypatch.setenv("STUCK_LLM_USD_KRW_RATE", "1380")
    provider = QueuedIntentProvider(
        [
            {
                "intent": "market_snapshot",
                "stock_query": "AAPL",
                "market": "US",
                "horizon_type": None,
                "analysis_mode": "quick",
                "source_hints": [],
                "needs_follow_up": False,
                "follow_up_question": None,
            },
        ]
    )

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "AAPL:NASDAQ"
        assert api_key == raw_serpapi_key
        return {
            "search_metadata": {"status": "Success"},
            "summary": {
                "title": "Apple Inc",
                "stock": "AAPL",
                "exchange": "NASDAQ",
                "extracted_price": 270.71,
                "currency": "USD",
                "price_movement": {
                    "percentage": 1.15,
                    "value": 3.08,
                    "movement": "Up",
                },
                "date": "Apr 29 2026, 12:17:30 AM UTC-04:00",
            },
            "graph": [
                {
                    "price": 267.5,
                    "date": "Apr 28 2026, 09:30 AM UTC-04:00",
                    "volume": 1000,
                },
                {
                    "price": 270.71,
                    "date": "Apr 29 2026, 12:17 AM UTC-04:00",
                    "volume": 2000,
                },
            ],
        }

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, raw_llm_key)

    resolved_quote = market_data_service.resolve_quote_from_text("애플", "KR")
    assert resolved_quote is not None
    assert resolved_quote.symbol == "AAPL"

    created_response = client.post(
        "/conversations",
        json={
            "content": "애플",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert created_response.status_code == 201
    created_body = created_response.json()
    assert created_body["status"] == "market_snapshot"
    assert created_body["missing_inputs"] == []
    assert created_body["market_snapshot"]["market"] == "US"
    assert created_body["market_snapshot"]["symbol"] == "AAPL"
    assert created_body["market_snapshot"]["chart_bars"][1]["close"] == 270.71
    assert created_body["messages"][-1]["market_snapshot"]["symbol"] == "AAPL"
    assert "Apple Inc (AAPL)" in created_body["messages"][-1]["content"]
    assert raw_llm_key not in created_response.text
    assert raw_serpapi_key not in created_response.text
    assert provider.analysis_requests == []
