from typing import List, Literal

from pydantic import BaseModel, Field

EvidenceStance = Literal["bullish", "neutral", "bearish"]
ProbabilityImpact = Literal["supports_buy", "supports_hold", "supports_sell"]
ScoringStatus = Literal["scored", "needs_evidence"]


class ScoringEvidenceInput(BaseModel):
    source_document_id: str
    stance: EvidenceStance
    weight: float = Field(ge=0.0, le=1.0)
    summary: str
    quote_excerpt: str


class ScoreCommand(BaseModel):
    analysis_request_id: str
    evidence_items: List[ScoringEvidenceInput]
    excluded_document_count: int = Field(ge=0)


class ScoreDriver(BaseModel):
    source_document_id: str
    stance: EvidenceStance
    weight: float
    probability_impact: ProbabilityImpact
    summary: str


class ScoreResponse(BaseModel):
    score_id: str
    analysis_request_id: str
    status: ScoringStatus
    buy_probability: float
    hold_probability: float
    sell_probability: float
    confidence_score: float
    expected_return_min_pct: float = 0.0
    expected_return_max_pct: float = 0.0
    downside_probability: float = 0.0
    similar_event_sample_count: int = 0
    similar_event_win_rate: float = 0.0
    similar_event_median_return_pct: float = 0.0
    confidence_factors: List[str] = Field(default_factory=list)
    drivers: List[ScoreDriver]
    rationale: str
