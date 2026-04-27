from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient

from app.main import create_app


ROOT_DIR = Path(__file__).resolve().parents[3]


def test_llm_credentials_are_encrypted_masked_and_use_generated_local_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("STUCK_LLM_CREDENTIAL_KEY", raising=False)
    state_path = tmp_path / "state.json"
    client = TestClient(create_app(state_path=state_path))
    raw_key = "sk-test-phase016-secret-value"

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": raw_key,
        },
    )
    read_response = client.get("/credentials/llm")

    assert response.status_code == 200
    assert raw_key not in response.text
    body = response.json()
    assert body["configured"] is True
    assert body["provider"] == "openai"
    assert body["model"] == "gpt-4o-mini"
    assert body["base_url"] == "https://api.openai.com/v1"
    assert body["api_key_mask"].startswith("sk-t")
    assert body["key_source"] == "generated_local"
    assert read_response.json() == body

    state_text = state_path.read_text()
    assert raw_key not in state_text
    assert "encrypted_api_key" in state_text
    assert (tmp_path / "stuck_llm_credential.key").exists()


def test_llm_credentials_can_use_environment_master_key_without_local_key_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUCK_LLM_CREDENTIAL_KEY", "phase-016-master-secret")
    state_path = tmp_path / "state.json"
    client = TestClient(create_app(state_path=state_path))

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-latest",
            "base_url": "https://api.anthropic.com/v1",
            "api_key": "sk-ant-phase016-secret-value",
        },
    )

    assert response.status_code == 200
    assert response.json()["key_source"] == "env"
    assert not (tmp_path / "stuck_llm_credential.key").exists()


def test_custom_llm_credentials_require_base_url(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.put(
        "/credentials/llm",
        json={
            "provider": "custom",
            "model": "local-model",
            "api_key": "local-secret",
        },
    )

    assert response.status_code == 422


def test_llm_credentials_can_be_deleted(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    payload = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key": "sk-delete-phase016-secret-value",
    }

    create_response = client.put("/credentials/llm", json=payload)
    delete_response = client.delete("/credentials/llm")
    read_response = client.get("/credentials/llm")

    assert create_response.status_code == 200
    assert delete_response.status_code == 200
    assert delete_response.json()["configured"] is False
    assert read_response.json()["configured"] is False


def test_setup_credentials_script_saves_encrypted_credentials(tmp_path: Path) -> None:
    state_path = tmp_path / "cli_state.json"
    raw_key = "sk-cli-phase016-secret-value"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "setup_credentials.py"),
            "--provider",
            "openai",
            "--model",
            "gpt-4o-mini",
            "--base-url",
            "https://api.openai.com/v1",
            "--api-key",
            raw_key,
            "--state-path",
            str(state_path),
            "--credential-key",
            "phase-016-cli-master",
        ],
        cwd=str(ROOT_DIR),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert raw_key not in result.stdout
    state_text = state_path.read_text()
    assert raw_key not in state_text
    assert "encrypted_api_key" in state_text
