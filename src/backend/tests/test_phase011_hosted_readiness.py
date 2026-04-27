from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_cors_preflight_allows_local_frontend_origin(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.options(
        "/settings",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"


def test_hosted_mode_requires_api_key_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STUCK_LLM_REQUIRE_API_KEY", "true")
    monkeypatch.setenv("STUCK_LLM_API_KEY", "phase-011-secret")
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    unauthenticated_response = client.get("/settings")
    health_response = client.get("/health")
    authenticated_response = client.get(
        "/settings",
        headers={"Authorization": "Bearer phase-011-secret"},
    )

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"] == "API key required"
    assert health_response.status_code == 200
    assert authenticated_response.status_code == 200


def test_hosted_mode_rejects_empty_configured_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STUCK_LLM_REQUIRE_API_KEY", "true")
    monkeypatch.setenv("STUCK_LLM_API_KEY", "")
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/settings", headers={"Authorization": "Bearer "})

    assert response.status_code == 401
    assert response.json()["detail"] == "API key required"


def test_analysis_rejects_bad_timestamps_and_oversized_content(tmp_path: Path) -> None:
    client = TestClient(
        create_app(state_path=tmp_path / "state.json"),
        raise_server_exceptions=False,
    )
    payload = {
        "market": "KR",
        "symbol": "005930",
        "stock_name": "Samsung Electronics",
        "horizon_type": "swing",
        "analysis_mode": "quick",
        "as_of_at": "2026-04-24",
        "source_documents": [
            {
                "source_type": "news",
                "source_name": "Local News",
                "title": "Memory demand improves",
                "published_at": "2026-04-24T08:30:00+09:00",
                "content_text": "Analysts see stronger memory demand.",
            }
        ],
    }

    missing_timezone_response = client.post("/analysis/requests", json=payload)
    payload["as_of_at"] = "2026-04-24T09:00:00+09:00"
    payload["source_documents"][0]["content_text"] = "x" * 8001
    oversized_response = client.post("/analysis/requests", json=payload)

    assert missing_timezone_response.status_code == 422
    assert oversized_response.status_code == 422


def test_analysis_response_hides_internal_prompt_material(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/analysis/requests",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "horizon_type": "swing",
            "analysis_mode": "quick",
            "as_of_at": "2026-04-24T09:00:00+09:00",
            "source_documents": [
                {
                    "source_type": "news",
                    "source_name": "Local News",
                    "title": "Memory demand improves",
                    "published_at": "2026-04-24T08:30:00+09:00",
                    "content_text": "Analysts see stronger memory demand and margin recovery.",
                }
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "system_instructions" not in body
    assert "prompt_context" not in body
    assert body["evidence_items"][0]["summary"] == "Memory demand improves"


def test_conversation_and_backtest_reject_invalid_payload_sizes_and_timestamps(
    tmp_path: Path,
) -> None:
    client = TestClient(
        create_app(state_path=tmp_path / "state.json"),
        raise_server_exceptions=False,
    )

    conversation_response = client.post("/conversations", json={"content": "x" * 4001})
    backtest_response = client.post(
        "/backtests/simulations",
        json={
            "market": "KR",
            "symbol": "005930",
            "entry_at": "not-a-date",
            "exit_at": "2026-04-24T15:30:00+09:00",
            "quantity": 1,
        },
    )

    assert conversation_response.status_code == 422
    assert backtest_response.status_code == 422
