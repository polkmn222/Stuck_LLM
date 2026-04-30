import json
import urllib.error
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import OpenAiCompatibleAnalysisProvider
from app.features.credentials import service as credential_service
from app.features.credentials.service import get_llm_credential_secret
from app.main import create_app

CEREBRAS_AVAILABLE_TEST_MODEL = "llama3.1-8b"


def test_llm_connection_test_uses_saved_cerebras_key_without_exposing_raw_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: List[Dict[str, Any]] = []
    raw_key = "csk-phase025-secret-value"

    def http_post(url, headers, payload, timeout_seconds):
        calls.append(
            {
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
                "url": url,
            }
        )
        return {"choices": [{"message": {"content": "ok"}}]}

    def provider_factory(network_policy):
        return OpenAiCompatibleAnalysisProvider(
            http_post=http_post,
            max_retries=0,
            network_policy=network_policy,
            resolver=lambda hostname, port: ["93.184.216.34"],
        )

    monkeypatch.setattr(
        credential_service,
        "_connection_test_provider",
        provider_factory,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    save_response = client.put(
        "/credentials/llm",
        json={
            "provider": "cerebras",
            "model": CEREBRAS_AVAILABLE_TEST_MODEL,
            "base_url": None,
            "api_key": raw_key,
        },
    )

    response = client.post("/credentials/llm/test")

    assert save_response.status_code == 200
    assert response.status_code == 200
    assert raw_key not in response.text
    body = response.json()
    assert body == {
        "configured": True,
        "status": "ok",
        "provider": "cerebras",
        "model": CEREBRAS_AVAILABLE_TEST_MODEL,
        "base_url": "https://api.cerebras.ai/v1",
        "key_source": "generated_local",
        "error_code": None,
        "message": "Connection test succeeded.",
    }
    assert calls[0]["url"] == "https://api.cerebras.ai/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {raw_key}"
    assert calls[0]["headers"]["Accept"] == "application/json"
    assert calls[0]["headers"]["User-Agent"].startswith("Stuck_LLM/")
    assert calls[0]["payload"]["model"] == CEREBRAS_AVAILABLE_TEST_MODEL
    assert calls[0]["payload"]["max_tokens"] == 8
    assert "response_format" not in calls[0]["payload"]
    assert raw_key not in json.dumps(calls[0]["payload"])


def test_llm_connection_test_maps_auth_errors_without_provider_detail(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw_key = "csk-phase025-auth-secret"

    def http_post(url, headers, payload, timeout_seconds):
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)

    def provider_factory(network_policy):
        return OpenAiCompatibleAnalysisProvider(
            http_post=http_post,
            max_retries=0,
            network_policy=network_policy,
            resolver=lambda hostname, port: ["93.184.216.34"],
        )

    monkeypatch.setattr(
        credential_service,
        "_connection_test_provider",
        provider_factory,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    client.put(
        "/credentials/llm",
        json={
            "provider": "cerebras",
            "model": CEREBRAS_AVAILABLE_TEST_MODEL,
            "base_url": None,
            "api_key": raw_key,
        },
    )

    response = client.post("/credentials/llm/test")

    assert response.status_code == 200
    assert raw_key not in response.text
    assert response.json() == {
        "configured": True,
        "status": "provider_error",
        "provider": "cerebras",
        "model": CEREBRAS_AVAILABLE_TEST_MODEL,
        "base_url": "https://api.cerebras.ai/v1",
        "key_source": "generated_local",
        "error_code": "auth_error",
        "message": "Authentication failed. Check the saved provider key.",
    }


def test_llm_connection_test_reports_setup_needed_without_credentials(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post("/credentials/llm/test")

    assert response.status_code == 200
    assert response.json() == {
        "configured": False,
        "status": "setup_needed",
        "provider": None,
        "model": None,
        "base_url": None,
        "key_source": None,
        "error_code": None,
        "message": "Save an LLM provider key before testing the connection.",
    }


def test_cerebras_environment_key_is_ignored_without_saved_user_credential(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OpenAI_API_Key", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("CEREBRAS_API_KEY", "csk-phase025-env-secret")
    monkeypatch.delenv("CEREBRAS_MODEL", raising=False)

    app = create_app(state_path=tmp_path / "state.json")
    secret = get_llm_credential_secret(
        app.state.local_store,
        app.state.credential_cipher,
    )

    assert secret is None
