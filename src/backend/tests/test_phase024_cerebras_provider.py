import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveProviderRequest,
    LlmProviderConfig,
    OpenAiCompatibleAnalysisProvider,
)
from app.features.analysis.schemas import SourceDocumentDecision
from app.features.credentials.service import get_llm_credential_secret
from app.main import create_app


def _document(source_id: str = "src_1") -> SourceDocumentDecision:
    return SourceDocumentDecision(
        id=source_id,
        source_type="news",
        source_name="Cerebras Test Wire",
        title="Demand improved",
        published_at="2026-04-24T08:00:00+09:00",
        content_text="Analysts see stronger demand.",
        included_in_analysis=True,
    )


def _cerebras_success_response(source_id: str = "src_1") -> Dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "summary": "Cerebras grounded summary.",
                            "evidence_items": [
                                {
                                    "source_document_id": source_id,
                                    "stance": "bullish",
                                    "weight": 0.7,
                                    "summary": "Demand improved",
                                    "quote_excerpt": "Analysts see stronger demand.",
                                }
                            ],
                        }
                    )
                }
            }
        ]
    }


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(child, key) for child in value.values())
    if isinstance(value, list):
        return any(_contains_key(child, key) for child in value)
    return False


def test_saved_cerebras_secret_uses_official_defaults_without_exposing_raw_key(
    tmp_path: Path,
) -> None:
    raw_key = "csk-phase024-secret"
    state_path = tmp_path / "state.json"
    app = create_app(state_path=state_path)
    client = TestClient(app)

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "cerebras",
            "model": "gpt-oss-120b",
            "base_url": None,
            "api_key": raw_key,
        },
    )

    secret = get_llm_credential_secret(
        app.state.local_store,
        app.state.credential_cipher,
    )

    assert response.status_code == 200
    assert raw_key not in response.text
    assert secret is not None
    assert secret.provider == "cerebras"
    assert secret.model == "gpt-oss-120b"
    assert secret.base_url == "https://api.cerebras.ai/v1"
    assert secret.api_key == raw_key
    assert raw_key not in state_path.read_text()


def test_cerebras_provider_uses_openai_compatible_endpoint_and_schema_shape() -> None:
    calls: List[Dict[str, Any]] = []

    def http_post(url, headers, payload, timeout_seconds):
        calls.append(
            {
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
                "url": url,
            }
        )
        return _cerebras_success_response()

    provider = OpenAiCompatibleAnalysisProvider(
        http_post=http_post,
        resolver=lambda hostname, port: ["93.184.216.34"],
    )

    output = provider.analyze(
        LiveProviderRequest(
            config=LlmProviderConfig(
                provider="cerebras",
                model="gpt-oss-120b",
                base_url="https://api.cerebras.ai/v1",
                api_key="csk-phase024-secret",
            ),
            messages=[{"role": "user", "content": "Return JSON."}],
            documents=[_document()],
            prompt_context="UNTRUSTED EVIDENCE ONLY",
            language="en",
        )
    )

    assert output.summary == "Cerebras grounded summary."
    assert calls[0]["url"] == "https://api.cerebras.ai/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer csk-phase024-secret"
    assert calls[0]["headers"]["Accept"] == "application/json"
    assert calls[0]["headers"]["User-Agent"].startswith("Stuck_LLM/")
    assert calls[0]["payload"]["model"] == "gpt-oss-120b"
    assert calls[0]["payload"]["response_format"]["type"] == "json_schema"
    assert not _contains_key(calls[0]["payload"]["response_format"], "minItems")
    assert not _contains_key(calls[0]["payload"]["response_format"], "maxItems")
