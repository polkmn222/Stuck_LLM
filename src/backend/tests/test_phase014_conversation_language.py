from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _clear_openai_environment(monkeypatch) -> None:
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


def test_korean_stock_typo_asks_for_confirmation_in_korean(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "삼성전가 주가 알려줘",
            "market": "KR",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["missing_inputs"] == ["stock_confirmation"]
    assert body["analysis_request"] is None
    assert body["messages"][1]["meta"] == "종목 확인 필요"
    assert "삼성전자" in body["messages"][1]["content"]
    assert "말씀이신가요" in body["messages"][1]["content"]


def test_follow_up_without_horizon_keeps_previous_stock_context(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    created_response = client.post(
        "/conversations",
        json={"content": "samsung analyze", "market": "KR", "analysis_mode": "quick"},
    )
    conversation_id = created_response.json()["conversation_id"]

    appended_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "buy", "market": "KR", "analysis_mode": "quick"},
    )

    assert appended_response.status_code == 200
    body = appended_response.json()
    assert body["status"] == "setup_needed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "005930"
    assert body["analysis_request"]["horizon_type"] == "swing"
    assert body["messages"][-1]["meta"] == "setup needed"
    assert "API key" in body["messages"][-1]["content"]


def test_horizon_follow_up_records_previous_stock_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_openai_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    created_response = client.post(
        "/conversations",
        json={"content": "samsung analyze", "market": "KR", "analysis_mode": "quick"},
    )
    conversation_id = created_response.json()["conversation_id"]

    appended_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Use a swing horizon.", "market": "KR", "analysis_mode": "quick"},
    )

    assert appended_response.status_code == 200
    body = appended_response.json()
    assert body["status"] == "setup_needed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "005930"
    assert body["analysis_request"]["horizon_type"] == "swing"
    assert body["messages"][-1]["meta"] == "setup needed"
    assert "API key" in body["messages"][-1]["content"]


def test_ready_reply_matches_korean_user_language(tmp_path: Path, monkeypatch) -> None:
    _clear_openai_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "삼성전자 분석해줘",
            "market": "KR",
            "horizon_type": "swing",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "setup_needed"
    assert body["messages"][1]["meta"] == "설정 필요"
    assert "API key" in body["messages"][1]["content"]
