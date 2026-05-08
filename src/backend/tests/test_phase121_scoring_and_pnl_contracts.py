import pytest
from pydantic import ValidationError

from app.features.backtest.schemas import BacktestResponse
from app.features.scoring.schemas import ScoreCommand, ScoringEvidenceInput
from app.features.scoring.service import score_evidence
from app.shared.state_store import LocalStateStore


def test_scoring_downside_probability_is_confidence_adjusted_not_sell_copy(tmp_path) -> None:
    store = LocalStateStore(tmp_path / "state.json")

    response = score_evidence(
        store,
        ScoreCommand(
            analysis_request_id="analysis_downside",
            excluded_document_count=2,
            evidence_items=[
                ScoringEvidenceInput(
                    source_document_id="src_constructive",
                    stance="bullish",
                    weight=0.8,
                    summary="Demand improved.",
                    quote_excerpt="Demand improved before cutoff.",
                ),
                ScoringEvidenceInput(
                    source_document_id="src_balanced",
                    stance="neutral",
                    weight=0.5,
                    summary="Valuation remains balanced.",
                    quote_excerpt="Valuation remains balanced.",
                ),
            ],
        ),
    )

    assert response.status == "scored"
    assert response.sell_probability < response.downside_probability < 100.0


def test_backtest_evaluation_kind_accepts_only_pnl_simulation_literal() -> None:
    payload = {
        "simulation_id": "backtest_literal",
        "analysis_request_id": None,
        "market": "US",
        "symbol": "AAPL",
        "entry_at": "2026-04-01T16:00:00-04:00",
        "exit_at": "2026-04-24T16:00:00-04:00",
        "entry_price": 190.0,
        "exit_price": 207.15,
        "quantity": 1.0,
        "gross_return_pct": 9.03,
        "gross_pnl": 17.15,
        "max_drawdown_pct": -2.38,
        "equity_curve": [],
        "source": "seeded_local_fixture",
    }

    assert BacktestResponse(**payload).evaluation_kind == "pnl_simulation"
    with pytest.raises(ValidationError):
        BacktestResponse(**{**payload, "evaluation_kind": "prediction_artifact"})
