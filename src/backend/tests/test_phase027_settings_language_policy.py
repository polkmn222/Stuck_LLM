import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.main import create_app


class CapturingIntentAndAnalysisProvider:
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
            summary="Provider summary in the requested language.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="neutral",
                    weight=0.5,
                    summary="Requested-language source handoff",
                    quote_excerpt="Eligible evidence was supplied.",
                )
            ],
        )


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


def test_explicit_korean_response_language_overrides_english_message_for_setup_needed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "setup_needed"
    assert body["messages"][-1]["meta"] == "설정 필요"
    assert "API key" in body["messages"][-1]["content"]


def test_explicit_english_response_language_overrides_korean_message_for_follow_up(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "삼성전자 분석해줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["messages"][-1]["meta"] == "missing horizon"
    assert "Which investment horizon" in body["messages"][-1]["content"]


def test_explicit_response_language_controls_chat_intent_and_live_analysis_prompts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    raw_key = "sk-phase027-language-secret"
    provider = CapturingIntentAndAnalysisProvider(
        {
            "intent": "stock_analysis",
            "stock_query": "삼성전자",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "source_hints": ["reddit"],
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
            "content": "삼성전자 스윙 분석해줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    assert provider.intent_requests[0].language == "en"
    assert provider.analysis_requests[0].language == "en"

    intent_messages = json.dumps(provider.intent_requests[0].messages)
    analysis_messages = json.dumps(provider.analysis_requests[0].messages)
    assert "requested_output_language" in intent_messages
    assert "English" in intent_messages
    assert "Required output language: English" in analysis_messages
    assert raw_key not in intent_messages
    assert raw_key not in analysis_messages
