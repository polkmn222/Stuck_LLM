from pathlib import Path
from typing import List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.main import create_app


class CapturingProvider:
    def __init__(self) -> None:
        self.requests: List[LiveProviderRequest] = []

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.requests.append(request)
        return LiveAnalysisOutput(
            summary=f"Selected {request.config.provider} / {request.config.model}.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=request.documents[0].id,
                    stance="neutral",
                    weight=0.5,
                    summary="Selected provider produced neutral evidence.",
                    quote_excerpt="Provider output stayed source grounded.",
                )
            ],
        )


def test_conversation_uses_explicitly_selected_llm_credential_without_secret_leaks(
    tmp_path: Path,
) -> None:
    provider = CapturingProvider()
    client = TestClient(
        create_app(
            state_path=tmp_path / "state.json",
            llm_analysis_provider=provider,
        )
    )

    openai_response = client.post(
        "/credentials/llm/profiles",
        json={
            "credential_id": "openai_research",
            "label": "OpenAI research",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-phase129-openai-secret",
            "make_active": False,
        },
    )
    cerebras_response = client.post(
        "/credentials/llm/profiles",
        json={
            "credential_id": "cerebras_fast",
            "label": "Cerebras fast",
            "provider": "cerebras",
            "model": "llama3.1-8b",
            "base_url": "https://api.cerebras.ai/v1",
            "api_key": "csk-phase129-cerebras-secret",
            "make_active": True,
        },
    )

    assert openai_response.status_code == 200
    assert cerebras_response.status_code == 200
    assert "sk-phase129-openai-secret" not in openai_response.text
    assert "csk-phase129-cerebras-secret" not in cerebras_response.text

    list_response = client.get("/credentials/llm/profiles")
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["active_credential_id"] == "cerebras_fast"
    assert {profile["credential_id"] for profile in body["credentials"]} == {
        "openai_research",
        "cerebras_fast",
    }
    assert "phase129" not in list_response.text

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "llm_credential_id": "openai_research",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "analysis_completed"
    assert provider.requests[-1].config.provider == "openai"
    assert provider.requests[-1].config.model == "gpt-4.1-mini"
    assert provider.requests[-1].config.api_key == "sk-phase129-openai-secret"
    assert "sk-phase129-openai-secret" not in response.text
    assert "csk-phase129-cerebras-secret" not in response.text


def test_active_llm_credential_can_be_selected_for_default_conversation_path(
    tmp_path: Path,
) -> None:
    provider = CapturingProvider()
    client = TestClient(
        create_app(
            state_path=tmp_path / "state.json",
            llm_analysis_provider=provider,
        )
    )

    client.post(
        "/credentials/llm/profiles",
        json={
            "credential_id": "openai_research",
            "label": "OpenAI research",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "api_key": "sk-phase129-openai-secret",
            "make_active": True,
        },
    )
    client.post(
        "/credentials/llm/profiles",
        json={
            "credential_id": "cerebras_fast",
            "label": "Cerebras fast",
            "provider": "cerebras",
            "model": "llama3.1-8b",
            "api_key": "csk-phase129-cerebras-secret",
            "make_active": False,
        },
    )

    select_response = client.patch("/credentials/llm/profiles/cerebras_fast/active")
    status_response = client.get("/credentials/llm")
    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert select_response.status_code == 200
    assert status_response.json()["credential_id"] == "cerebras_fast"
    assert response.status_code == 201
    assert provider.requests[-1].config.provider == "cerebras"
    assert provider.requests[-1].config.api_key == "csk-phase129-cerebras-secret"
    assert "csk-phase129-cerebras-secret" not in response.text
