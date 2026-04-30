from pathlib import Path

from fastapi.testclient import TestClient

from app.features.credentials.service import get_llm_credential_secret
from app.main import create_app


def _clear_llm_environment(monkeypatch) -> None:
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


def test_missing_saved_key_keeps_llm_in_setup_needed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _clear_llm_environment(monkeypatch)
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
    assert "API key" in body["messages"][-1]["content"]


def test_saved_cerebras_credential_is_selectable_and_decrypted_without_raw_key_exposure(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    raw_key = "csk-phase035-selected-cerebras"
    app = create_app(state_path=state_path)
    client = TestClient(app)

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "cerebras",
            "model": "llama3.1-8b",
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
    assert response.json()["provider"] == "cerebras"
    assert response.json()["base_url"] == "https://api.cerebras.ai/v1"
    assert secret is not None
    assert secret.provider == "cerebras"
    assert secret.api_key == raw_key
    assert raw_key not in state_path.read_text()


def test_saved_openai_credential_remains_user_selectable_for_later_provider_testing(
    tmp_path: Path,
) -> None:
    raw_key = "sk-phase035-selected-openai"
    app = create_app(state_path=tmp_path / "state.json")
    client = TestClient(app)

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": None,
            "api_key": raw_key,
        },
    )
    secret = get_llm_credential_secret(
        app.state.local_store,
        app.state.credential_cipher,
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "openai"
    assert response.json()["base_url"] == "https://api.openai.com/v1"
    assert secret is not None
    assert secret.provider == "openai"
    assert secret.api_key == raw_key


def test_environment_keys_are_ignored_when_no_user_key_is_saved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _clear_llm_environment(monkeypatch)
    monkeypatch.setenv("CEREBRAS_API_KEY", "csk-phase035-env-cerebras")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-phase035-env-openai")
    monkeypatch.delenv("CEREBRAS_MODEL", raising=False)
    state_path = tmp_path / "state.json"
    app = create_app(state_path=state_path)

    secret = get_llm_credential_secret(
        app.state.local_store,
        app.state.credential_cipher,
    )

    assert secret is None
    assert not state_path.exists() or "csk-phase035-env-cerebras" not in state_path.read_text()
    assert not state_path.exists() or "sk-phase035-env-openai" not in state_path.read_text()
