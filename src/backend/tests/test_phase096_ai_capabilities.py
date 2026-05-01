from fastapi.testclient import TestClient

from app.main import create_app


def test_ai_capabilities_route_reports_provider_matrix_without_secrets(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/ai/capabilities")

    assert response.status_code == 200
    body = response.json()
    serialized = response.text
    assert body["providers"]["openai"]["stock_analysis"]["level"] == "supported"
    assert body["providers"]["local_model"]["stock_analysis"]["level"] == "unsupported"
    assert any(item["key"] == "prediction_artifact" for item in body["prompt_inventory"])
    assert "api_key" not in serialized.lower()
    assert "sk-" not in serialized
