from __future__ import annotations

from app.evals import EvalCase, classify_source_quality, evaluate_case, evidence_quality_weight
from app.features.analysis.schemas import (
    AnalysisResponse,
    EvidenceItem,
    SourceAuditSummary,
    SourceDocumentDecision,
)


AS_OF_AT = "2026-04-24T09:00:00+09:00"


def _source(
    source_id: str,
    *,
    source_type: str,
    source_name: str,
    title: str = "Source title",
    published_at: str = "2026-04-24T08:30:00+09:00",
    relevance_score: float | None = 0.8,
    included: bool = True,
    exclusion_reason: str | None = None,
) -> SourceDocumentDecision:
    return SourceDocumentDecision(
        id=source_id,
        source_type=source_type,
        source_name=source_name,
        url=f"https://example.test/{source_id}",
        title=title,
        published_at=published_at,
        content_text="Demand improved before cutoff.",
        relevance_score=relevance_score,
        included_in_analysis=included,
        exclusion_reason=exclusion_reason,
    )


def _analysis(documents: list[SourceDocumentDecision]) -> AnalysisResponse:
    included_documents = [document for document in documents if document.included_in_analysis]
    return AnalysisResponse(
        analysis_request_id="analysis_quality_001",
        status="completed" if included_documents else "needs_evidence",
        market="KR",
        symbol="005930",
        stock_name="Samsung Electronics",
        horizon_type="swing",
        analysis_mode="quick",
        as_of_at=AS_OF_AT,
        included_document_count=len(included_documents),
        excluded_document_count=len(documents) - len(included_documents),
        source_audit=SourceAuditSummary(
            included_by_source_type={
                document.source_type: sum(
                    1
                    for candidate in included_documents
                    if candidate.source_type == document.source_type
                )
                for document in included_documents
            },
            excluded_by_reason={
                document.exclusion_reason or "unknown": sum(
                    1
                    for candidate in documents
                    if not candidate.included_in_analysis
                    and candidate.exclusion_reason == document.exclusion_reason
                )
                for document in documents
                if not document.included_in_analysis
            },
            prompt_document_ids=[document.id for document in included_documents],
        ),
        source_documents=documents,
        evidence_items=[
            EvidenceItem(
                source_document_id=document.id,
                stance="neutral",
                weight=0.4,
                summary=document.title,
                quote_excerpt="Demand improved before cutoff.",
            )
            for document in included_documents
        ],
        summary="Grounded summary.",
    )


def test_source_quality_scores_official_fresh_above_social_when_relevance_matches() -> None:
    official = _source(
        "src_official",
        source_type="official_filing",
        source_name="DART",
        relevance_score=0.7,
    )
    social = _source(
        "src_social",
        source_type="social",
        source_name="Forum",
        relevance_score=0.7,
    )

    official_quality = classify_source_quality(official, AS_OF_AT)
    social_quality = classify_source_quality(social, AS_OF_AT)

    assert official_quality.reliability == "official"
    assert official_quality.freshness == "fresh"
    assert social_quality.reliability == "social"
    assert official_quality.quality_score > social_quality.quality_score
    assert evidence_quality_weight(official, AS_OF_AT) > evidence_quality_weight(
        social,
        AS_OF_AT,
    )


def test_source_quality_uses_metadata_not_official_claims_in_title() -> None:
    social_claiming_official = _source(
        "src_claim",
        source_type="social",
        source_name="Forum",
        title="Official SEC filing excerpt posted by user",
    )

    quality = classify_source_quality(social_claiming_official, AS_OF_AT)

    assert quality.reliability == "social"
    assert quality.quality_score < 0.5


def test_source_quality_warns_for_unknown_and_low_reliability_sources() -> None:
    analysis = _analysis(
        [
            _source("src_unknown", source_type="misc", source_name="Unknown Blog"),
            _source("src_social", source_type="social", source_name="Forum"),
        ]
    )

    result = evaluate_case(EvalCase(case_id="quality-warnings", analysis=analysis))
    warning_rule_ids = {
        finding.rule_id for finding in result.findings if finding.severity == "warning"
    }

    assert {
        "source_quality.unknown_reliability",
        "source_quality.low_reliability",
    }.issubset(warning_rule_ids)


def test_source_quality_future_dated_source_has_zero_quality_and_warning() -> None:
    future = _source(
        "src_future",
        source_type="news",
        source_name="News Wire",
        published_at="2026-04-24T09:30:00+09:00",
        included=False,
        exclusion_reason="published_after_as_of_at",
    )

    quality = classify_source_quality(future, AS_OF_AT)
    result = evaluate_case(EvalCase(case_id="future-quality", analysis=_analysis([future])))

    assert quality.freshness == "future"
    assert quality.quality_score == 0.0
    assert evidence_quality_weight(future, AS_OF_AT) == 0.0
    assert "source_quality.future_dated_source" in {
        finding.rule_id for finding in result.findings if finding.severity == "warning"
    }


def test_source_quality_relevance_score_adjusts_weight_deterministically() -> None:
    higher_relevance = _source(
        "src_high",
        source_type="news",
        source_name="News Wire",
        relevance_score=0.9,
    )
    lower_relevance = _source(
        "src_low",
        source_type="news",
        source_name="News Wire",
        relevance_score=0.3,
    )

    assert evidence_quality_weight(higher_relevance, AS_OF_AT) > evidence_quality_weight(
        lower_relevance,
        AS_OF_AT,
    )
