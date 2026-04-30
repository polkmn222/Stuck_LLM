from fastapi.testclient import TestClient

from app.main import create_app


def test_scoring_converts_weighted_evidence_to_probabilities(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/scoring/evaluate",
        json={
            "analysis_request_id": "analysis_001",
            "excluded_document_count": 1,
            "evidence_items": [
                {
                    "source_document_id": "src_bull",
                    "stance": "bullish",
                    "weight": 0.6,
                    "summary": "Memory demand improves",
                    "quote_excerpt": "Demand and margin recovery improved.",
                },
                {
                    "source_document_id": "src_neutral",
                    "stance": "neutral",
                    "weight": 0.4,
                    "summary": "Valuation is fair",
                    "quote_excerpt": "Valuation remains close to peers.",
                },
                {
                    "source_document_id": "src_bear",
                    "stance": "bearish",
                    "weight": 0.2,
                    "summary": "FX headwind",
                    "quote_excerpt": "FX is a modest margin headwind.",
                },
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "scored"
    assert body["buy_probability"] == 36.4
    assert body["hold_probability"] == 45.4
    assert body["sell_probability"] == 18.2
    assert round(
        body["buy_probability"] + body["hold_probability"] + body["sell_probability"],
        1,
    ) == 100.0
    assert body["confidence_score"] == 0.69
    assert body["expected_return_min_pct"] < body["expected_return_max_pct"]
    assert body["downside_probability"] == body["sell_probability"]
    assert body["similar_event_sample_count"] > 0
    assert body["similar_event_win_rate"] > 0
    assert body["drivers"][0] == {
        "source_document_id": "src_bull",
        "stance": "bullish",
        "weight": 0.6,
        "probability_impact": "supports_buy",
        "summary": "Memory demand improves",
    }


def test_scoring_handles_empty_evidence_without_fabricating_probabilities(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/scoring/evaluate",
        json={
            "analysis_request_id": "analysis_empty",
            "excluded_document_count": 2,
            "evidence_items": [],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_evidence"
    assert body["buy_probability"] == 0.0
    assert body["hold_probability"] == 0.0
    assert body["sell_probability"] == 0.0
    assert body["confidence_score"] == 0.0
    assert body["rationale"] == "No eligible evidence was available for scoring."


def test_scoring_bearish_evidence_supports_sell_probability(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/scoring/evaluate",
        json={
            "analysis_request_id": "analysis_bearish",
            "excluded_document_count": 0,
            "evidence_items": [
                {
                    "source_document_id": "src_warning",
                    "stance": "bearish",
                    "weight": 0.7,
                    "summary": "Demand warning",
                    "quote_excerpt": "Demand weakened.",
                }
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "scored"
    assert body["sell_probability"] > body["buy_probability"]
    assert body["drivers"][0]["probability_impact"] == "supports_sell"
