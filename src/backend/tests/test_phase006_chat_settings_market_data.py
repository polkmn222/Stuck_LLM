from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_settings_update_persists_across_app_instances(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    first_client = TestClient(create_app(state_path=state_path))

    response = first_client.patch(
        "/settings",
        json={
            "provider": "claude",
            "analysis_mode": "deep",
            "default_market": "US",
            "default_horizon": "swing",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "provider": "claude",
        "analysis_mode": "deep",
        "default_market": "US",
        "default_horizon": "swing",
    }

    second_client = TestClient(create_app(state_path=state_path))

    persisted_response = second_client.get("/settings")

    assert persisted_response.status_code == 200
    assert persisted_response.json() == {
        "provider": "claude",
        "analysis_mode": "deep",
        "default_market": "US",
        "default_horizon": "swing",
    }


def test_conversation_without_horizon_asks_one_follow_up(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={"content": "Should I buy Samsung Electronics now?"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["horizon"]
    assert body["analysis_request"] is None
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
    assert "investment horizon" in body["messages"][1]["content"]


def test_conversation_with_required_inputs_records_market_snapshot(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    client = TestClient(create_app(state_path=state_path))

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
    assert body["status"] == "ready_for_analysis"
    assert body["missing_inputs"] == []
    assert body["analysis_request"] == {
        "market": "KR",
        "symbol": "005930",
        "stock_name": "Samsung Electronics",
        "horizon_type": "swing",
        "analysis_mode": "quick",
    }
    assert body["market_snapshot"]["symbol"] == "005930"
    assert body["market_snapshot"]["currency"] == "KRW"
    assert "market snapshot" in body["messages"][1]["content"]
    assert "LLM analysis is not connected yet" in body["messages"][1]["content"]

    persisted_client = TestClient(create_app(state_path=state_path))
    persisted_response = persisted_client.get(f"/conversations/{body['conversation_id']}")

    assert persisted_response.status_code == 200
    assert persisted_response.json()["messages"] == body["messages"]


def test_message_endpoint_appends_to_existing_conversation(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    created_response = client.post(
        "/conversations",
        json={
            "content": "Should I buy Samsung Electronics?",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )
    conversation_id = created_response.json()["conversation_id"]

    appended_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Compare that with AAPL.",
            "market": "US",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert appended_response.status_code == 200
    body = appended_response.json()
    assert body["conversation_id"] == conversation_id
    assert len(body["messages"]) == 4
    assert body["analysis_request"]["symbol"] == "AAPL"


def test_seeded_market_data_quote_is_available(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/KR/005930")

    assert response.status_code == 200
    assert response.json() == {
        "market": "KR",
        "symbol": "005930",
        "name": "Samsung Electronics",
        "exchange": "KRX",
        "currency": "KRW",
        "last_price": 72000.0,
        "as_of_at": "2026-04-24T15:30:00+09:00",
        "source": "seeded_local_fixture",
    }
