from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.features.analysis.schemas import SourceDocumentDecision
from app.shared.datetime_utils import parse_aware_datetime

SourceReliability = Literal["official", "news", "social", "unknown"]
SourceFreshness = Literal["fresh", "stale", "future"]

OFFICIAL_SOURCE_TYPES = {
    "official_filing",
    "regulatory_filing",
    "sec_filing",
    "dart_filing",
    "company_filing",
}
OFFICIAL_SOURCE_NAMES = {
    "dart",
    "edgar",
    "sec edgar",
    "financial supervisory service",
}
NEWS_SOURCE_TYPES = {
    "news",
    "naver_news",
    "tavily_news",
    "gnews_news",
    "us_news",
    "global_news",
}
SOCIAL_SOURCE_TYPES = {
    "social",
    "reddit",
    "forum",
    "message_board",
    "naver_discussion",
}
RELIABILITY_SCORES: dict[SourceReliability, float] = {
    "official": 1.0,
    "news": 0.7,
    "social": 0.35,
    "unknown": 0.25,
}
FRESHNESS_SCORES: dict[SourceFreshness, float] = {
    "fresh": 1.0,
    "stale": 0.7,
    "future": 0.0,
}


@dataclass(frozen=True)
class SourceQuality:
    reliability: SourceReliability
    freshness: SourceFreshness
    quality_score: float
    warnings: list[str]


def _reliability(document: SourceDocumentDecision) -> SourceReliability:
    source_type = document.source_type.strip().lower()
    source_name = document.source_name.strip().lower()
    if source_type in OFFICIAL_SOURCE_TYPES or source_name in OFFICIAL_SOURCE_NAMES:
        return "official"
    if source_type in NEWS_SOURCE_TYPES:
        return "news"
    if source_type in SOCIAL_SOURCE_TYPES:
        return "social"
    return "unknown"


def _freshness(document: SourceDocumentDecision, as_of_at: str) -> SourceFreshness:
    published_at = parse_aware_datetime(
        document.published_at,
        error_message="Datetime must be a valid ISO 8601 value.",
        timezone_error_message="Datetime must include a timezone offset.",
    )
    cutoff = parse_aware_datetime(
        as_of_at,
        error_message="Datetime must be a valid ISO 8601 value.",
        timezone_error_message="Datetime must include a timezone offset.",
    )
    if published_at > cutoff:
        return "future"
    age_seconds = (cutoff - published_at).total_seconds()
    if age_seconds <= 60 * 60 * 24 * 14:
        return "fresh"
    return "stale"


def _warnings(
    reliability: SourceReliability,
    freshness: SourceFreshness,
) -> list[str]:
    warnings: list[str] = []
    if freshness == "future":
        warnings.append("source_quality.future_dated_source")
    if reliability == "unknown":
        warnings.append("source_quality.unknown_reliability")
    elif reliability == "social":
        warnings.append("source_quality.low_reliability")
    return warnings


def classify_source_quality(
    document: SourceDocumentDecision,
    as_of_at: str,
) -> SourceQuality:
    reliability = _reliability(document)
    freshness = _freshness(document, as_of_at)
    if freshness == "future":
        quality_score = 0.0
    else:
        quality_score = round(
            RELIABILITY_SCORES[reliability] * FRESHNESS_SCORES[freshness],
            3,
        )
    return SourceQuality(
        reliability=reliability,
        freshness=freshness,
        quality_score=quality_score,
        warnings=_warnings(reliability, freshness),
    )


def evidence_quality_weight(
    document: SourceDocumentDecision,
    as_of_at: str,
) -> float:
    quality = classify_source_quality(document, as_of_at)
    if quality.quality_score == 0:
        return 0.0
    relevance = document.relevance_score
    if relevance is None:
        relevance = 0.5
    bounded_relevance = max(0.0, min(relevance, 1.0))
    return round(quality.quality_score * (0.5 + bounded_relevance * 0.5), 3)
