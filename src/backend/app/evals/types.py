from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from app.features.analysis.schemas import AnalysisResponse
from app.features.scoring.schemas import ScoreResponse

EvalSeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    analysis: AnalysisResponse
    score: Optional[ScoreResponse] = None


@dataclass(frozen=True)
class EvalFinding:
    rule_id: str
    severity: EvalSeverity
    message: str
    source_id: Optional[str] = None


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    findings: list[EvalFinding] = field(default_factory=list)


@dataclass(frozen=True)
class EvalReport:
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[EvalResult]
