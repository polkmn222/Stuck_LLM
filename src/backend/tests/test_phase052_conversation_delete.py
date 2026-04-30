from fastapi.testclient import TestClient

from app.main import create_app


def _create_snapshot_conversation(client: TestClient, content: str, market: str = "US") -> str:
    response = client.post(
        "/conversations",
        json={
            "content": content,
            "market": market,
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )
    assert response.status_code == 201
    return str(response.json()["conversation_id"])


def test_delete_conversation_removes_only_the_selected_thread(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    first_id = _create_snapshot_conversation(client, "AAPL", "US")
    second_id = _create_snapshot_conversation(client, "Apple", "US")

    delete_response = client.delete(f"/conversations/{first_id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted_count": 1}
    assert client.get(f"/conversations/{first_id}").status_code == 404

    list_response = client.get("/conversations")

    assert list_response.status_code == 200
    summaries = list_response.json()["conversations"]
    assert [summary["conversation_id"] for summary in summaries] == [second_id]


def test_clear_conversations_removes_all_saved_threads(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    _create_snapshot_conversation(client, "AAPL", "US")
    _create_snapshot_conversation(client, "Apple", "US")

    clear_response = client.delete("/conversations")

    assert clear_response.status_code == 200
    assert clear_response.json() == {"deleted_count": 2}
    assert client.get("/conversations").json() == {"conversations": []}


def test_delete_missing_conversation_returns_not_found(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.delete("/conversations/conv_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
