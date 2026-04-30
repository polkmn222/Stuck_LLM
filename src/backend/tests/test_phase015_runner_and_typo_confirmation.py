from pathlib import Path
from typing import Callable, Optional, cast

from fastapi.testclient import TestClient

from app.features.market_data import service as market_data_service
from app.features.market_data.schemas import MarketQuote
from app.main import create_app


ROOT_DIR = Path(__file__).resolve().parents[3]


class QuoteCandidateProtocol:
    quote: MarketQuote
    canonical_name: str


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


def test_likely_stock_typo_is_not_exact_alias_but_has_confirmation_candidate() -> None:
    assert market_data_service.resolve_quote_from_text("삼성전가 주가 알려줘", "KR") is None

    candidate_resolver = cast(
        Optional[Callable[[str, str], Optional[QuoteCandidateProtocol]]],
        getattr(market_data_service, "find_quote_confirmation_candidate", None),
    )
    assert candidate_resolver is not None

    candidate = candidate_resolver("삼성전가 주가 알려줘", "KR")

    assert candidate is not None
    assert candidate.quote.symbol == "005930"
    assert candidate.canonical_name == "삼성전자"


def test_typo_with_horizon_still_requires_stock_confirmation(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "삼성전사 스윙 분석해줘",
            "market": "KR",
            "analysis_mode": "quick",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["stock_confirmation"]
    assert body["analysis_request"] is None
    assert "삼성전자" in body["messages"][1]["content"]


def test_affirmative_follow_up_confirms_stock_candidate_and_records_horizon(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_openai_environment(monkeypatch)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    created_response = client.post(
        "/conversations",
        json={"content": "삼성전가 주가 알려줘", "market": "KR", "analysis_mode": "quick"},
    )
    conversation_id = created_response.json()["conversation_id"]

    appended_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "네, 스윙으로 봐줘", "market": "KR", "analysis_mode": "quick"},
    )

    assert appended_response.status_code == 200
    body = appended_response.json()
    assert body["status"] == "setup_needed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "005930"
    assert body["analysis_request"]["horizon_type"] == "swing"
    assert "API key" in body["messages"][-1]["content"]


def test_non_affirmative_follow_up_does_not_confirm_stock_candidate(tmp_path: Path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    created_response = client.post(
        "/conversations",
        json={"content": "삼성전가 주가 알려줘", "market": "KR", "analysis_mode": "quick"},
    )
    conversation_id = created_response.json()["conversation_id"]

    appended_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "네이버", "market": "KR", "analysis_mode": "quick"},
    )

    assert appended_response.status_code == 200
    body = appended_response.json()
    assert body["status"] == "needs_input"
    assert body["missing_inputs"] == ["stock"]
    assert body["analysis_request"] is None


def test_run_all_opens_frontend_by_default_and_can_disable_auto_open() -> None:
    run_all_text = (ROOT_DIR / "run-all.sh").read_text()

    assert 'AUTO_OPEN_BROWSER="${AUTO_OPEN_BROWSER:-1}"' in run_all_text
    assert 'open_frontend "$FRONTEND_URL"' in run_all_text
    assert 'if [ "$AUTO_OPEN_BROWSER" = "1" ]; then' in run_all_text


def test_run_all_ctrl_c_uses_shutdown_trap_and_execs_server_processes() -> None:
    run_all_text = (ROOT_DIR / "run-all.sh").read_text()

    assert "shutdown() {" in run_all_text
    assert "trap shutdown INT TERM" in run_all_text
    assert "trap cleanup EXIT" in run_all_text
    assert "exec python3 -m uvicorn app.main:app" in run_all_text
    assert "exec npm run dev" in run_all_text
    assert 'wait "$FRONTEND_PID" 2>/dev/null || true' in run_all_text
    assert 'wait "$BACKEND_PID" 2>/dev/null || true' in run_all_text
