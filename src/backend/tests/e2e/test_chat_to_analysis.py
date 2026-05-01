from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from e2e.helpers import E2EPredictionProvider, clear_provider_environment, save_openai_credential


def test_chat_to_prediction_analysis_happy_path_persists_retrievable_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_provider_environment(monkeypatch)
    provider = E2EPredictionProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    save_openai_credential(client, "sk-phase102-e2e-secret")

    response = client.post(
        "/conversations",
        json={
            "content": "애플 예측",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    conversation_id = body["conversation_id"]
    assert body["status"] == "analysis_completed"
    assert body["analysis_request"]["symbol"] == "AAPL"
    assert body["analysis_result"]["score_result"]["status"] == "scored"
    assert body["analysis_result"]["source_audit"]["prompt_document_ids"]
    assert provider.analysis_requests
    assert "sk-phase102-e2e-secret" not in response.text

    restored = client.get(f"/conversations/{conversation_id}")

    assert restored.status_code == 200
    assert restored.json()["conversation_id"] == conversation_id
    assert restored.json()["status"] == "analysis_completed"
