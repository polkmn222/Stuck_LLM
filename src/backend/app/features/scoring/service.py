from typing import Any, Dict, List, Tuple, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.scoring.schemas import (
    ProbabilityImpact,
    ScoreCommand,
    ScoreDriver,
    ScoreResponse,
    ScoringEvidenceInput,
)
from app.shared.state_store import LocalStateStore, State


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())


def _impact_for(item: ScoringEvidenceInput) -> ProbabilityImpact:
    if item.stance == "bullish":
        return "supports_buy"
    if item.stance == "bearish":
        return "supports_sell"
    return "supports_hold"


def _drivers(items: List[ScoringEvidenceInput]) -> List[ScoreDriver]:
    return [
        ScoreDriver(
            source_document_id=item.source_document_id,
            stance=item.stance,
            weight=item.weight,
            probability_impact=_impact_for(item),
            summary=item.summary,
        )
        for item in items
    ]


def _weighted_stance_totals(items: List[ScoringEvidenceInput]) -> Tuple[float, float, float]:
    bullish = sum(item.weight for item in items if item.stance == "bullish")
    neutral = sum(item.weight for item in items if item.stance == "neutral")
    bearish = sum(item.weight for item in items if item.stance == "bearish")
    return bullish, neutral, bearish


def _probabilities(items: List[ScoringEvidenceInput]) -> Tuple[float, float, float]:
    bullish, neutral, bearish = _weighted_stance_totals(items)
    raw_buy = 0.2 + bullish
    raw_hold = 0.6 + neutral
    raw_sell = 0.2 + bearish
    total = raw_buy + raw_hold + raw_sell

    buy = round(raw_buy / total * 100, 1)
    sell = round(raw_sell / total * 100, 1)
    hold = round(100.0 - buy - sell, 1)
    return buy, hold, sell


def _confidence(items: List[ScoringEvidenceInput], excluded_document_count: int) -> float:
    total_weight = min(sum(item.weight for item in items), 2.0)
    evidence_count = min(len(items), 5)
    confidence = 0.35 + total_weight * 0.2 + evidence_count * 0.05
    confidence -= excluded_document_count * 0.05
    return round(max(0.2, min(confidence, 0.95)), 2)


def _expected_return_range(
    buy_probability: float,
    sell_probability: float,
    confidence_score: float,
) -> Tuple[float, float]:
    directional_edge = (buy_probability - sell_probability) / 100.0
    midpoint = directional_edge * 4.0
    uncertainty_width = max(1.2, (1.0 - confidence_score) * 8.0)
    low = round(midpoint - uncertainty_width / 2.0, 1)
    high = round(midpoint + uncertainty_width / 2.0, 1)
    return low, high


def _similar_event_stats(items: List[ScoringEvidenceInput]) -> Tuple[int, float, float]:
    bullish, neutral, bearish = _weighted_stance_totals(items)
    if bullish > bearish and bullish >= neutral:
        return 8, 62.5, 1.4
    if bearish > bullish and bearish >= neutral:
        return 6, 33.3, -1.1
    return 10, 50.0, 0.2


def score_evidence(store: LocalStateStore, command: ScoreCommand) -> ScoreResponse:
    if not command.evidence_items:
        response = ScoreResponse(
            score_id=f"score_{uuid4().hex}",
            analysis_request_id=command.analysis_request_id,
            status="needs_evidence",
            buy_probability=0.0,
            hold_probability=0.0,
            sell_probability=0.0,
            confidence_score=0.0,
            drivers=[],
            rationale="No eligible evidence was available for scoring.",
        )
    else:
        buy, hold, sell = _probabilities(command.evidence_items)
        confidence_score = _confidence(
            command.evidence_items,
            command.excluded_document_count,
        )
        expected_return_min, expected_return_max = _expected_return_range(
            buy,
            sell,
            confidence_score,
        )
        sample_count, win_rate, median_return = _similar_event_stats(command.evidence_items)
        response = ScoreResponse(
            score_id=f"score_{uuid4().hex}",
            analysis_request_id=command.analysis_request_id,
            status="scored",
            buy_probability=buy,
            hold_probability=hold,
            sell_probability=sell,
            confidence_score=confidence_score,
            expected_return_min_pct=expected_return_min,
            expected_return_max_pct=expected_return_max,
            downside_probability=sell,
            similar_event_sample_count=sample_count,
            similar_event_win_rate=win_rate,
            similar_event_median_return_pct=median_return,
            drivers=_drivers(command.evidence_items),
            rationale=(
                "Probabilities are normalized from evidence stance weights with a hold baseline; "
                "confidence reflects evidence count, total eligible weight, and excluded-source penalty; "
                "expected return range is a rough five-trading-day estimate from directional edge "
                "and confidence, not a calibrated forecast; similar-event calibration is a local "
                "baseline slot for future historical matching."
            ),
        )

    def mutate(state: State) -> ScoreResponse:
        state["scores"][response.score_id] = _model_dump(response)
        return response

    return store.update(mutate)
