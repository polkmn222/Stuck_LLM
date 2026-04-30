from __future__ import annotations

import json
import socket
import urllib.error
from pathlib import Path
from typing import Any, Dict, List

import pytest
from pydantic import SecretStr

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderError,
    LiveProviderRequest,
    LlmProviderConfig,
    OpenAiCompatibleAnalysisProvider,
    ProviderNetworkPolicy,
)
from app.features.analysis.schemas import AnalysisRequestCommand, SourceDocumentDecision
from app.features.analysis.service import LIVE_MAX_SOURCE_DOCUMENTS, create_live_analysis
from app.features.credentials.schemas import LlmCredentialUpsert
from app.features.credentials.service import save_llm_credential
from app.shared.credential_crypto import CredentialCipher
from app.shared.runtime_config import RuntimeConfig
from app.shared.state_store import LocalStateStore


class CapturingProvider:
    def __init__(self) -> None:
        self.requests: List[LiveProviderRequest] = []

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.requests.append(request)
        return LiveAnalysisOutput(
            summary="Budgeted live summary.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=request.documents[0].id,
                    stance="neutral",
                    weight=0.4,
                    summary="Budgeted source",
                    quote_excerpt="Budgeted quote",
                )
            ],
        )


def _document(source_id: str = "src_1") -> SourceDocumentDecision:
    return SourceDocumentDecision(
        id=source_id,
        source_type="news",
        source_name="Policy Wire",
        title="Memory demand improves",
        published_at="2026-04-24T08:00:00+09:00",
        content_text="Analysts see stronger memory demand.",
        included_in_analysis=True,
    )


def _request(
    config: LlmProviderConfig,
    documents: List[SourceDocumentDecision] | None = None,
) -> LiveProviderRequest:
    return LiveProviderRequest(
        config=config,
        messages=[{"role": "user", "content": "Return JSON."}],
        documents=documents or [_document()],
        prompt_context="UNTRUSTED EVIDENCE ONLY",
        language="en",
    )


def _success_response(source_id: str = "src_1") -> Dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "summary": "Grounded provider summary.",
                            "evidence_items": [
                                {
                                    "source_document_id": source_id,
                                    "stance": "bullish",
                                    "weight": 0.7,
                                    "summary": "Demand improved",
                                    "quote_excerpt": "Demand improved.",
                                }
                            ],
                        }
                    )
                }
            }
        ]
    }


def _http_error(status_code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.example.test/v1/chat/completions",
        status_code,
        "provider error",
        {},
        None,
    )


def test_non_official_hostname_resolving_to_private_ip_is_rejected_before_http_call() -> None:
    provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: pytest.fail(
            f"DNS-unsafe URL should not be called: {url}"
        ),
        resolver=lambda hostname, port: ["10.0.0.12"],
    )

    with pytest.raises(LiveProviderError) as error:
        provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="openai",
                    model="gpt-4.1-mini",
                    base_url="https://public-provider.example/v1",
                    api_key="sk-test",
                )
            )
        )

    assert error.value.code == "invalid_base_url"


def test_custom_provider_requires_explicit_opt_in_before_http_call() -> None:
    provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: pytest.fail(
            f"custom provider should require opt-in before calling: {url}"
        ),
        resolver=lambda hostname, port: ["93.184.216.34"],
    )

    with pytest.raises(LiveProviderError) as error:
        provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="custom",
                    model="openai-compatible-model",
                    base_url="https://llm.example.com/v1",
                    api_key="sk-test",
                )
            )
        )

    assert error.value.code == "invalid_base_url"


def test_custom_public_provider_allowed_with_opt_in_and_safe_dns() -> None:
    calls: List[str] = []
    provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: calls.append(url)
        or _success_response(),
        network_policy=ProviderNetworkPolicy(allow_custom_provider=True),
        resolver=lambda hostname, port: ["93.184.216.34"],
    )

    output = provider.analyze(
        _request(
            LlmProviderConfig(
                provider="custom",
                model="openai-compatible-model",
                base_url="https://llm.example.com/v1",
                api_key="sk-test",
            )
        )
    )

    assert output.summary == "Grounded provider summary."
    assert calls == ["https://llm.example.com/v1/chat/completions"]


def test_hosted_custom_provider_requires_allowlisted_base_url() -> None:
    blocked = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: pytest.fail(
            f"hosted custom provider should require allowlist: {url}"
        ),
        network_policy=ProviderNetworkPolicy(
            hosted_mode=True,
            allow_custom_provider=True,
            provider_egress_allowlist=[],
        ),
        resolver=lambda hostname, port: ["93.184.216.34"],
    )

    with pytest.raises(LiveProviderError) as error:
        blocked.analyze(
            _request(
                LlmProviderConfig(
                    provider="custom",
                    model="openai-compatible-model",
                    base_url="https://llm.example.com/v1",
                    api_key="sk-test",
                )
            )
        )
    assert error.value.code == "invalid_base_url"

    calls: List[str] = []
    allowed = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: calls.append(url)
        or _success_response(),
        network_policy=ProviderNetworkPolicy(
            hosted_mode=True,
            allow_custom_provider=True,
            provider_egress_allowlist=["https://llm.example.com/v1"],
        ),
        resolver=lambda hostname, port: ["93.184.216.34"],
    )

    allowed.analyze(
        _request(
            LlmProviderConfig(
                provider="custom",
                model="openai-compatible-model",
                base_url="https://llm.example.com/v1",
                api_key="sk-test",
            )
        )
    )

    assert calls == ["https://llm.example.com/v1/chat/completions"]


def test_local_private_custom_provider_is_dev_only_and_metadata_is_always_blocked() -> None:
    dev_calls: List[str] = []
    dev_provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: dev_calls.append(url)
        or _success_response(),
        network_policy=ProviderNetworkPolicy(
            allow_custom_provider=True,
            allow_private_base_url=True,
        ),
    )
    hosted_provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: pytest.fail(
            f"hosted private custom provider should not be called: {url}"
        ),
        network_policy=ProviderNetworkPolicy(
            hosted_mode=True,
            allow_custom_provider=True,
            allow_private_base_url=True,
            provider_egress_allowlist=["http://localhost:11434/v1"],
        ),
    )

    dev_provider.analyze(
        _request(
            LlmProviderConfig(
                provider="custom",
                model="llama-local",
                base_url="http://localhost:11434/v1",
                api_key="local-dev-key",
            )
        )
    )
    assert dev_calls == ["http://localhost:11434/v1/chat/completions"]

    with pytest.raises(LiveProviderError) as hosted_error:
        hosted_provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="custom",
                    model="llama-local",
                    base_url="http://localhost:11434/v1",
                    api_key="local-dev-key",
                )
            )
        )
    assert hosted_error.value.code == "invalid_base_url"

    with pytest.raises(LiveProviderError) as metadata_error:
        dev_provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="custom",
                    model="llama-local",
                    base_url="http://169.254.169.254/latest",
                    api_key="local-dev-key",
                )
            )
        )
    assert metadata_error.value.code == "invalid_base_url"


def test_runtime_config_exposes_provider_policy_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("STUCK_LLM_REQUIRE_API_KEY", "true")
    monkeypatch.setenv("STUCK_LLM_ALLOW_CUSTOM_PROVIDER", "true")
    monkeypatch.setenv("STUCK_LLM_ALLOW_PRIVATE_BASE_URL", "true")
    monkeypatch.setenv(
        "STUCK_LLM_PROVIDER_EGRESS_ALLOWLIST",
        "https://llm.example.com/v1, https://api.openai.com/v1",
    )

    from app.shared.runtime_config import load_runtime_config

    config = load_runtime_config()
    assert config.allow_custom_provider is True
    assert config.allow_private_base_url is True
    assert config.provider_egress_allowlist == [
        "https://llm.example.com/v1",
        "https://api.openai.com/v1",
    ]


def test_provider_network_policy_is_derived_from_runtime_config() -> None:
    config = RuntimeConfig(
        cors_origins=[],
        require_api_key=True,
        api_key="hosted-secret",
        credential_key=None,
        credential_key_path=None,
        allow_custom_provider=True,
        allow_private_base_url=True,
        provider_egress_allowlist=["https://llm.example.com/v1"],
    )

    policy = ProviderNetworkPolicy.from_runtime_config(config)

    assert policy.hosted_mode is True
    assert policy.allow_custom_provider is True
    assert policy.allow_private_base_url is True
    assert policy.provider_egress_allowlist == ["https://llm.example.com/v1"]


def test_retry_limited_to_transient_429_and_503() -> None:
    attempts = 0
    slept: List[float] = []

    def http_post(url, headers, payload, timeout_seconds):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise _http_error(429)
        if attempts == 2:
            raise _http_error(503)
        return _success_response()

    provider = OpenAiCompatibleAnalysisProvider(
        http_post=http_post,
        sleep=slept.append,
    )

    output = provider.analyze(
        _request(
            LlmProviderConfig(
                provider="openai",
                model="gpt-4.1-mini",
                base_url="https://api.openai.com/v1",
                api_key="sk-test",
            )
        )
    )

    assert output.summary == "Grounded provider summary."
    assert attempts == 3
    assert slept == [0.5, 1.5]


def test_auth_errors_are_not_retried() -> None:
    attempts = 0

    def http_post(url, headers, payload, timeout_seconds):
        nonlocal attempts
        attempts += 1
        raise _http_error(401)

    provider = OpenAiCompatibleAnalysisProvider(http_post=http_post, sleep=lambda delay: None)

    with pytest.raises(LiveProviderError) as error:
        provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="openai",
                    model="gpt-4.1-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="sk-test",
                )
            )
        )

    assert error.value.code == "auth_error"
    assert attempts == 1


def test_timeout_maps_to_user_safe_timeout_error() -> None:
    provider = OpenAiCompatibleAnalysisProvider(
        http_post=lambda url, headers, payload, timeout_seconds: (_ for _ in ()).throw(
            socket.timeout("raw socket detail")
        )
    )

    with pytest.raises(LiveProviderError) as error:
        provider.analyze(
            _request(
                LlmProviderConfig(
                    provider="openai",
                    model="gpt-4.1-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="sk-test",
                )
            )
        )

    assert error.value.code == "timeout"
    assert "raw socket detail" not in str(error.value)


def test_live_prompt_budget_excludes_extra_sources_before_provider_call(tmp_path: Path) -> None:
    store = LocalStateStore(tmp_path / "state.json")
    cipher = CredentialCipher(
        configured_key="phase-021-test-master",
        local_key_path=tmp_path / "credential.key",
    )
    save_llm_credential(
        store,
        cipher,
        LlmCredentialUpsert(
            provider="openai",
            model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
            api_key=SecretStr("sk-phase021-secret"),
        ),
    )
    provider = CapturingProvider()

    response = create_live_analysis(
        store=store,
        cipher=cipher,
        provider=provider,
        language="en",
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
                    "source_name": f"Wire {index}",
                    "title": f"Demand update {index}",
                    "published_at": "2026-04-24T08:00:00+09:00",
                    "content_text": "Long source text " + ("x" * 1200),
                }
                for index in range(LIVE_MAX_SOURCE_DOCUMENTS + 5)
            ],
        ),
    )

    assert response.status == "completed"
    assert len(provider.requests[0].documents) <= LIVE_MAX_SOURCE_DOCUMENTS
    assert response.included_document_count == len(provider.requests[0].documents)
    assert any(
        document.exclusion_reason == "prompt_budget"
        for document in response.source_documents
    )
    assert "x" * 900 not in provider.requests[0].prompt_context
