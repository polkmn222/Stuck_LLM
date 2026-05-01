from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)


class E2EPredictionProvider:
    def __init__(self) -> None:
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return {
            "intent": "stock_analysis",
            "stock_query": "AAPL",
            "market": "US",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="E2E Apple evidence supports a constructive setup.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Eligible evidence supports the setup.",
                    quote_excerpt="Market evidence is stable.",
                )
            ],
        )


def clear_provider_environment(monkeypatch) -> None:
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
        "SERPAPI_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


def save_openai_credential(client: TestClient, raw_key: str) -> None:
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
