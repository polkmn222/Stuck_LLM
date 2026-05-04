import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatCompletionProviderRequest,
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.main import create_app
from e2e.helpers import clear_provider_environment, save_openai_credential


class MatrixProvider:
    def __init__(self) -> None:
        self.completion_requests: List[ChatCompletionProviderRequest] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        current_message = self._current_message(request)
        lowered = current_message.lower()
        if "news" in lowered or "뉴스" in current_message:
            return {
                "intent": "news_digest",
                "stock_query": "AAPL",
                "market": "US",
                "horizon_type": None,
                "analysis_mode": "quick",
                "source_hints": ["tavily_news"],
                "needs_follow_up": False,
                "follow_up_question": None,
            }
        if "predict" in lowered or "예측" in current_message:
            return {
                "intent": "stock_analysis",
                "stock_query": "AAPL",
                "market": "US",
                "horizon_type": "swing",
                "analysis_mode": "quick",
                "source_hints": ["global_macro"],
                "needs_follow_up": False,
                "follow_up_question": None,
            }
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

    def complete_chat(self, request: ChatCompletionProviderRequest) -> str:
        self.completion_requests.append(request)
        if "news_digest" in request.messages[-1]["content"] or "articles" in request.messages[-1]["content"]:
            return "Apple news summary from deterministic matrix provider."
        return "Simple chat response from deterministic matrix provider."

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="Matrix Apple evidence supports a constructive setup.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Eligible matrix evidence supports the setup.",
                    quote_excerpt="Market evidence is stable before cutoff.",
                )
            ],
        )

    def _current_message(self, request: Any) -> str:
        prompt = request.messages[-1]["content"]
        marker = '{"allowed_analysis_modes"'
        payload_start = prompt.find(marker)
        if payload_start < 0:
            return prompt
        payload = json.loads(prompt[payload_start:])
        return str(payload.get("current_message") or "")


def _fake_news_fetch_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    _ = url, headers, timeout_seconds
    query = str(payload.get("query")) if payload is not None else "Apple Inc AAPL news"
    return {
        "results": [
            {
                "title": "Apple earnings preview highlights services growth",
                "url": "https://example.com/apple-earnings",
                "content": "Investors are watching services and device demand.",
                "published_date": "2026-04-29T13:00:00-04:00",
                "score": 0.92,
                "query": query,
            }
        ]
    }


def test_conversation_matrix_covers_chat_news_prediction_cache_and_pnl(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    clear_provider_environment(monkeypatch)
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase118")
    monkeypatch.setattr(news_digest_service, "_fetch_json", _fake_news_fetch_json)
    provider = MatrixProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    raw_key = "sk-phase118-matrix-secret"
    save_openai_credential(client, raw_key)

    chat = client.post(
        "/conversations",
        json={
            "content": "hello",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )
    news = client.post(
        "/conversations",
        json={
            "content": "AAPL latest news",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )
    first_prediction = client.post(
        "/conversations",
        json={
            "content": "AAPL prediction",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )
    second_prediction = client.post(
        "/conversations",
        json={
            "content": "AAPL prediction",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )
    pnl = client.post(
        "/conversations",
        json={
            "content": "what if I bought AAPL on 2026-04-01",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert chat.status_code == 201
    assert news.status_code == 201
    assert first_prediction.status_code == 201
    assert second_prediction.status_code == 201
    assert pnl.status_code == 201
    assert chat.json()["status"] == "chat_completed"
    assert news.json()["status"] == "news_digest"
    assert news.json()["news_digest"]["provider_runs"][0]["provider"] == "tavily_news"
    assert first_prediction.json()["status"] == "analysis_completed"
    assert first_prediction.json()["analysis_result"]["score_result"]["confidence_factors"]
    assert second_prediction.json()["status"] == "analysis_completed"
    assert len(provider.analysis_requests) == 1
    assert pnl.json()["status"] == "pnl_simulation"
    assert pnl.json()["backtest_result"]["evaluation_kind"] == "pnl_simulation"
    assert raw_key not in (
        chat.text
        + news.text
        + first_prediction.text
        + second_prediction.text
        + pnl.text
    )
