from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


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
    assert body["missing_inputs"] == ["horizon"]
    assert body["analysis_request"] is None
    assert body["messages"][-1]["meta"] == "missing horizon"
    assert "investment horizon" in body["messages"][-1]["content"]


def test_horizon_follow_up_records_previous_stock_context(tmp_path: Path) -> None:
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
    assert body["status"] == "ready_for_analysis"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "005930"
    assert body["analysis_request"]["horizon_type"] == "swing"
    assert body["messages"][-1]["meta"] == "market snapshot recorded"
    assert "LLM analysis is not connected yet" in body["messages"][-1]["content"]


def test_ready_reply_matches_korean_user_language(tmp_path: Path) -> None:
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
    assert body["status"] == "ready_for_analysis"
    assert body["messages"][1]["meta"] == "시장 스냅샷 기록"
    assert "LLM 분석은 아직 연결되지 않았습니다" in body["messages"][1]["content"]
