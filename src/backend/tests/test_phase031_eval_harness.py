from __future__ import annotations

from app.evals import EvalCase, evaluate_case, evaluate_cases
from app.features.analysis.schemas import (
    AnalysisResponse,
    EvidenceItem,
    SourceAuditSummary,
    SourceDocumentDecision,
)
from app.features.scoring.schemas import ScoreDriver, ScoreResponse


def _source(
    source_id: str,
    *,
    included: bool = True,
    published_at: str = "2026-04-24T08:30:00+09:00",
    exclusion_reason: str | None = None,
) -> SourceDocumentDecision:
    return SourceDocumentDecision(
        id=source_id,
        source_type="news",
        source_name="Example News",
        url=f"https://example.test/{source_id}",
        title=f"Source {source_id}",
        published_at=published_at,
        content_text="Demand improved before cutoff.",
        included_in_analysis=included,
        exclusion_reason=exclusion_reason,
    )


def _evidence(source_id: str) -> EvidenceItem:
    return EvidenceItem(
        source_document_id=source_id,
        stance="bullish",
        weight=0.6,
        summary="Demand improved",
        quote_excerpt="Demand improved before cutoff.",
    )


def _analysis(
    *,
    documents: list[SourceDocumentDecision] | None = None,
    evidence_items: list[EvidenceItem] | None = None,
    prompt_document_ids: list[str] | None = None,
    status: str = "completed",
) -> AnalysisResponse:
    source_documents = documents or [_source("src_before")]
    included_count = sum(1 for document in source_documents if document.included_in_analysis)
    excluded_count = len(source_documents) - included_count
    return AnalysisResponse(
        analysis_request_id="analysis_eval_001",
        status=status,  # type: ignore[arg-type]
        market="KR",
        symbol="005930",
        stock_name="Samsung Electronics",
        horizon_type="swing",
        analysis_mode="quick",
        as_of_at="2026-04-24T09:00:00+09:00",
        included_document_count=included_count,
        excluded_document_count=excluded_count,
        source_audit=SourceAuditSummary(
            included_by_source_type={"news": included_count} if included_count else {},
            excluded_by_reason={"published_after_as_of_at": excluded_count}
            if excluded_count
            else {},
            prompt_document_ids=prompt_document_ids
            if prompt_document_ids is not None
            else [document.id for document in source_documents if document.included_in_analysis],
        ),
        source_documents=source_documents,
        evidence_items=evidence_items
        if evidence_items is not None
        else [_evidence("src_before")],
        summary="Grounded summary.",
    )


def _score(
    *,
    drivers: list[ScoreDriver] | None = None,
    buy: float = 36.4,
    hold: float = 45.4,
    sell: float = 18.2,
    confidence: float = 0.69,
    status: str = "scored",
) -> ScoreResponse:
    return ScoreResponse(
        score_id="score_eval_001",
        analysis_request_id="analysis_eval_001",
        status=status,  # type: ignore[arg-type]
        buy_probability=buy,
        hold_probability=hold,
        sell_probability=sell,
        confidence_score=confidence,
        drivers=drivers
        if drivers is not None
        else [
            ScoreDriver(
                source_document_id="src_before",
                stance="bullish",
                weight=0.6,
                probability_impact="supports_buy",
                summary="Demand improved",
            )
        ],
        rationale="Normalized evidence weights.",
    )


def test_eval_case_passes_for_grounded_cutoff_safe_outputs() -> None:
    result = evaluate_case(EvalCase(case_id="clean", analysis=_analysis(), score=_score()))

    assert result.passed is True
    assert result.findings == []


def test_eval_case_flags_future_sources_that_are_included_prompted_or_cited() -> None:
    analysis = _analysis(
        documents=[
            _source("src_before"),
            _source(
                "src_future",
                published_at="2026-04-24T09:30:00+09:00",
                included=True,
            ),
        ],
        evidence_items=[_evidence("src_before"), _evidence("src_future")],
        prompt_document_ids=["src_before", "src_future"],
    )

    result = evaluate_case(EvalCase(case_id="future-source", analysis=analysis))

    assert result.passed is False
    assert {
        "analysis.cutoff.future_source_included",
        "analysis.cutoff.future_source_prompted",
        "analysis.cutoff.future_source_cited",
    }.issubset({finding.rule_id for finding in result.findings})


def test_eval_case_flags_unknown_and_excluded_evidence_sources() -> None:
    analysis = _analysis(
        documents=[
            _source("src_before"),
            _source(
                "src_excluded",
                included=False,
                published_at="2026-04-24T09:30:00+09:00",
                exclusion_reason="published_after_as_of_at",
            ),
        ],
        evidence_items=[_evidence("src_missing"), _evidence("src_excluded")],
    )

    result = evaluate_case(EvalCase(case_id="bad-grounding", analysis=analysis))

    assert result.passed is False
    assert {
        "analysis.grounding.unknown_evidence_source",
        "analysis.grounding.excluded_evidence_source",
    }.issubset({finding.rule_id for finding in result.findings})


def test_eval_case_flags_invalid_scoring_probabilities_and_driver_grounding() -> None:
    score = _score(
        buy=120.0,
        hold=20.0,
        sell=10.0,
        drivers=[
            ScoreDriver(
                source_document_id="src_missing",
                stance="bullish",
                weight=0.5,
                probability_impact="supports_buy",
                summary="Missing source",
            )
        ],
    )

    result = evaluate_case(EvalCase(case_id="bad-score", analysis=_analysis(), score=score))

    assert result.passed is False
    assert {
        "scoring.probability.out_of_range",
        "scoring.probability.invalid_sum",
        "scoring.grounding.unknown_driver_source",
    }.issubset({finding.rule_id for finding in result.findings})


def test_eval_case_flags_high_confidence_without_evidence() -> None:
    analysis = _analysis(evidence_items=[], status="needs_evidence")
    score = _score(drivers=[], buy=0.0, hold=0.0, sell=0.0, confidence=0.85)

    result = evaluate_case(EvalCase(case_id="unsupported-confidence", analysis=analysis, score=score))

    assert result.passed is False
    assert "scoring.confidence.high_without_evidence" in {
        finding.rule_id for finding in result.findings
    }


def test_eval_report_summarizes_multiple_cases() -> None:
    report = evaluate_cases(
        [
            EvalCase(case_id="clean", analysis=_analysis(), score=_score()),
            EvalCase(
                case_id="future",
                analysis=_analysis(
                    documents=[
                        _source(
                            "src_future",
                            published_at="2026-04-24T09:30:00+09:00",
                            included=True,
                        )
                    ],
                    evidence_items=[_evidence("src_future")],
                    prompt_document_ids=["src_future"],
                ),
            ),
        ]
    )

    assert report.total_cases == 2
    assert report.passed_cases == 1
    assert report.failed_cases == 1
    assert report.results[1].case_id == "future"
