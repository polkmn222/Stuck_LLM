from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.main import create_app
from app.shared.state_store import LocalStateStore


class CacheablePredictionProvider:
    def __init__(self) -> None:
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

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

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="Cached Apple evidence supports a constructive setup.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Eligible market evidence is stable.",
                    quote_excerpt="The evidence set can be safely reused.",
                )
            ],
        )


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


def test_repeated_prediction_reuses_artifact_without_recalling_provider(
    tmp_path: Path,
    monkeypatch,
) -> None:
    for name in ("NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET", "TAVILY_API_KEY", "GNEWS_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    provider = CacheablePredictionProvider()
    state_path = tmp_path / "state.json"
    client = TestClient(create_app(state_path=state_path, llm_analysis_provider=provider))
    raw_key = "sk-phase095-prediction-secret"
    _save_openai_credential(client, raw_key)

    first = client.post(
        "/conversations",
        json={
            "content": "애플 예측",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )
    second = client.post(
        "/conversations",
        json={
            "content": "애플 예측",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    state = LocalStateStore(state_path).read()
    serialized_state = str(state)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["status"] == "analysis_completed"
    assert second.json()["status"] == "analysis_completed"
    assert len(provider.analysis_requests) == 1
    assert len(state["prediction_artifacts"]) == 1
    assert raw_key not in serialized_state
    assert "LIVE_SYSTEM_INSTRUCTIONS" not in serialized_state

