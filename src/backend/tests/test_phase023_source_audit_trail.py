from pathlib import Path
from typing import List

from pydantic import SecretStr

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.features.analysis.schemas import AnalysisRequestCommand
from app.features.analysis.service import create_live_analysis
from app.features.credentials.schemas import LlmCredentialUpsert
from app.features.credentials.service import save_llm_credential
from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore


class CapturingProvider:
    def __init__(self) -> None:
        self.requests: List[LiveProviderRequest] = []

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.requests.append(request)
        return LiveAnalysisOutput(
            summary="Audited source summary.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=request.documents[0].id,
                    stance="bullish",
                    weight=0.7,
                    summary="Demand improved before cutoff",
                    quote_excerpt="Demand improved before cutoff.",
                )
            ],
        )


def test_live_analysis_returns_source_audit_with_warnings_flags_and_prompt_ids(
    tmp_path: Path,
) -> None:
    store = LocalStateStore(tmp_path / "state.json")
    cipher = CredentialCipher(
        configured_key="phase-023-test-master",
        local_key_path=tmp_path / "credential.key",
    )
    save_llm_credential(
        store,
        cipher,
        LlmCredentialUpsert(
            provider="openai",
            model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
            api_key=SecretStr("sk-phase023-audit-secret"),
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
            source_warnings=[
                "missing_credential:naver_news",
                "provider_error:gnews_news",
            ],
            source_documents=[
                {
                    "source_type": "tavily_news",
                    "source_name": "Tavily Search",
                    "url": "https://example.com/demand",
                    "title": "Demand improved before cutoff",
                    "published_at": "2026-04-24T08:30:00+09:00",
                    "fetched_at": "2026-04-24T09:00:00+09:00",
                    "content_text": "Demand improved before cutoff.",
                    "language": "en",
                    "adapter": "tavily_news",
                    "relevance_score": 0.86,
                    "safety_flags": ["external_api", "untrusted_source_text"],
                },
                {
                    "source_type": "gnews_news",
                    "source_name": "GNews Wire",
                    "url": "https://example.com/future",
                    "title": "Future source should be excluded",
                    "published_at": "2026-04-24T09:01:00+09:00",
                    "fetched_at": "2026-04-24T09:00:00+09:00",
                    "content_text": "FUTURE_SOURCE_DO_NOT_PROMPT",
                    "language": "en",
                    "adapter": "gnews_news",
                    "relevance_score": 0.82,
                    "safety_flags": ["external_api", "untrusted_source_text"],
                },
            ],
        ),
        provider=provider,
        language="en",
    )

    assert response.status == "completed"
    assert response.source_audit.source_warnings == [
        "missing_credential:naver_news",
        "provider_error:gnews_news",
    ]
    assert response.source_audit.included_by_source_type == {"tavily_news": 1}
    assert response.source_audit.excluded_by_reason == {"published_after_as_of_at": 1}
    assert response.source_audit.prompt_document_ids == [
        response.source_documents[0].id
    ]
    assert response.source_documents[0].adapter == "tavily_news"
    assert response.source_documents[0].relevance_score == 0.86
    assert response.source_documents[0].safety_flags == [
        "external_api",
        "untrusted_source_text",
    ]
    assert response.source_documents[1].exclusion_reason == "published_after_as_of_at"
    assert [document.id for document in provider.requests[0].documents] == [
        response.source_documents[0].id
    ]
    assert "FUTURE_SOURCE_DO_NOT_PROMPT" not in provider.requests[0].prompt_context
