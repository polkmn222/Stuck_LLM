from pathlib import Path
from typing import List

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderError,
    LiveProviderRequest,
    LlmProviderConfig,
    OpenAiCompatibleAnalysisProvider,
)
from app.features.analysis.schemas import AnalysisRequestCommand
from app.features.analysis.service import create_live_analysis
from app.features.credentials.schemas import LlmCredentialUpsert
from app.features.credentials.service import save_llm_credential
from app.main import create_app
from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore


class CapturingProvider:
    def __init__(self, summary: str = "Grounded live summary.") -> None:
        self.summary = summary
        self.requests: List[LiveProviderRequest] = []

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary=self.summary,
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Memory demand improves",
                    quote_excerpt="US data center orders remain firm.",
                )
            ],
        )


class FailingProvider:
    def __init__(self, code: str) -> None:
        self.code = code

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        raise LiveProviderError(self.code, "provider detail must stay server-side")


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


def _clear_openai_environment(monkeypatch) -> None:
    for name in [
        "OPENAI_API_KEY",
        "OpenAI_API_Key",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "CEREBRAS_API_KEY",
        "CEREBRAS_MODEL",
        "CEREBRAS_BASE_URL",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_chat_ready_request_without_credentials_returns_english_setup_needed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_openai_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "setup_needed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "005930"
    assert body["market_snapshot"]["symbol"] == "005930"
    assert body["messages"][-1]["meta"] == "setup needed"
    assert "API key" in body["messages"][-1]["content"]
    assert "LLM analysis is not connected yet" not in body["messages"][-1]["content"]


def test_chat_ready_request_without_credentials_returns_korean_setup_needed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_openai_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "삼성전자 스윙 분석해줘",
            "market": "KR",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "setup_needed"
    assert body["messages"][-1]["meta"] == "설정 필요"
    assert "API key" in body["messages"][-1]["content"]


def test_chat_ready_request_uses_decrypted_credential_with_mocked_live_provider(
    tmp_path: Path,
) -> None:
    raw_key = "sk-phase018-live-secret"
    provider = CapturingProvider(summary="Samsung demand summary from live provider.")
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert body["messages"][-1]["meta"] == "live analysis"
    assert "Samsung demand summary from live provider." in body["messages"][-1]["content"]
    assert provider.requests[0].config.provider == "openai"
    assert provider.requests[0].config.model == "gpt-4.1-mini"
    assert provider.requests[0].config.base_url == "https://api.openai.com/v1"
    assert provider.requests[0].config.api_key == raw_key
    assert provider.requests[0].documents
    assert "UNTRUSTED EVIDENCE ONLY" in provider.requests[0].prompt_context


@pytest.mark.parametrize(
    ("error_code", "expected_text"),
    [
        ("auth_error", "provider authentication failed"),
        ("rate_limited", "provider is rate limiting"),
        ("timeout", "provider timed out"),
    ],
)
def test_chat_ready_request_maps_provider_errors_without_internal_details(
    tmp_path: Path,
    error_code: str,
    expected_text: str,
) -> None:
    raw_key = f"sk-phase018-{error_code}"
    client = TestClient(
        create_app(
            state_path=tmp_path / f"{error_code}.json",
            llm_analysis_provider=FailingProvider(error_code),
        )
    )
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "provider_error"
    assert body["messages"][-1]["meta"] == "provider error"
    assert expected_text in body["messages"][-1]["content"]
    assert "provider detail must stay server-side" not in body["messages"][-1]["content"]


def test_chat_ready_request_maps_malformed_output_to_provider_error_without_fallback(
    tmp_path: Path,
) -> None:
    raw_key = "sk-phase128-malformed-provider-error"
    client = TestClient(
        create_app(
            state_path=tmp_path / "malformed_provider_error.json",
            llm_analysis_provider=FailingProvider("malformed_output"),
        )
    )
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "provider_error"
    assert body["messages"][-1]["meta"] == "provider error"
    assistant_content = body["messages"][-1]["content"]
    assert "local evidence fallback" not in assistant_content
    assert "probabilities" not in assistant_content
    assert body["analysis_result"]["status"] == "provider_error"
    assert body["analysis_result"]["provider_error_code"] == "malformed_output"
    assert body["analysis_result"]["evidence_items"] == []
    assert body["analysis_result"]["score_result"] is None
    assert "provider detail must stay server-side" not in body["messages"][-1]["content"]


def test_live_analysis_prompt_includes_cutoff_equality_and_excludes_future_sources(
    tmp_path: Path,
) -> None:
    store = LocalStateStore(tmp_path / "state.json")
    cipher = CredentialCipher(
        configured_key="phase-018-test-master",
        local_key_path=tmp_path / "credential.key",
    )
    save_llm_credential(
        store,
        cipher,
        LlmCredentialUpsert(
            provider="openai",
            model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
            api_key=SecretStr("sk-cutoff-secret"),
        ),
    )
    provider = CapturingProvider()

    response = create_live_analysis(
        store=store,
        cipher=cipher,
        command=AnalysisRequestCommand(
            market="KR",
            symbol="005930",
            stock_name="Samsung Electronics",
            horizon_type="swing",
            analysis_mode="deep",
            as_of_at="2026-04-24T09:00:00+09:00",
            source_documents=[
                {
                    "source_type": "news",
                    "source_name": "Equal Wire",
                    "title": "Equal cutoff memo",
                    "published_at": "2026-04-24T09:00:00+09:00",
                    "content_text": "Equal timestamp demand improvement.",
                },
                {
                    "source_type": "news",
                    "source_name": "Future Wire",
                    "title": "Future leak memo",
                    "published_at": "2026-04-24T09:00:01+09:00",
                    "content_text": "FUTURE_LEAK_DO_NOT_SEND",
                },
            ],
        ),
        provider=provider,
        language="en",
    )

    assert response.status == "completed"
    assert response.included_document_count == 1
    assert response.excluded_document_count == 1
    assert response.source_documents[0].included_in_analysis is True
    assert response.source_documents[1].exclusion_reason == "published_after_as_of_at"
    assert [document.title for document in provider.requests[0].documents] == [
        "Equal cutoff memo"
    ]
    assert "Future leak memo" not in provider.requests[0].prompt_context
    assert "FUTURE_LEAK_DO_NOT_SEND" not in provider.requests[0].prompt_context


def test_openai_compatible_provider_maps_malformed_structured_output() -> None:
    provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: {
            "choices": [{"message": {"content": '{"summary": "missing evidence"}'}}]
        }
    )

    with pytest.raises(LiveProviderError) as error:
        provider.analyze(
            LiveProviderRequest(
                config=LlmProviderConfig(
                    provider="openai",
                    model="gpt-4.1-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="sk-test",
                ),
                messages=[],
                documents=[],
                prompt_context="UNTRUSTED EVIDENCE ONLY",
                language="en",
            )
        )

    assert error.value.code == "malformed_output"
