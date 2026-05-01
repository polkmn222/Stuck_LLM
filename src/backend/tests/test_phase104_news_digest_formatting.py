import json

from app.features.conversations.news_digest_formatting import (
    digest_with_llm_output,
    extract_json_object,
)
from app.features.news_digest.schemas import NewsArticle, NewsDigest, NewsSearchRun


def _article(article_id: str, title: str, rank: int) -> NewsArticle:
    return NewsArticle(
        id=article_id,
        title=title,
        url=f"https://example.com/{article_id}",
        source="Example Markets",
        published_at="2026-04-30T09:00:00Z",
        snippet="Original snippet",
        provider="tavily_news",
        query="Apple news",
        rank=rank,
        category="other",
    )


def _digest() -> NewsDigest:
    return NewsDigest(
        digest_id="digest_test",
        status="completed",
        market="US",
        symbol="AAPL",
        stock_name="Apple Inc",
        query="Apple news",
        generated_at="2026-04-30T09:05:00Z",
        summary="Original summary",
        key_points=[],
        important_articles=[_article("news_1", "Apple earnings", 0)],
        additional_articles=[_article("news_2", "Apple services", 1)],
        provider_runs=[
            NewsSearchRun(
                provider="tavily_news",
                query="Apple news",
                result_count=2,
                status="completed",
            )
        ],
        warnings=[],
    )


def test_extract_json_object_accepts_fenced_json_with_surrounding_text() -> None:
    parsed = extract_json_object(
        "Here is the digest:\n```json\n{\"summary\": \"updated\"}\n```\nDone."
    )

    assert parsed == {"summary": "updated"}


def test_digest_with_llm_output_updates_summary_and_matching_articles() -> None:
    digest = _digest()
    output = json.dumps(
        {
            "summary": "Updated source-grounded summary",
            "articles": [
                {
                    "id": "news_1",
                    "headline_ko": "애플 실적 핵심",
                    "summary_ko": "서비스 매출이 주목됩니다.",
                    "category": "earnings",
                },
                {
                    "id": "news_2",
                    "headline_ko": "서비스 업데이트",
                    "summary_ko": "카탈로그가 확대됐습니다.",
                    "category": "unsupported",
                },
            ],
        }
    )

    updated = digest_with_llm_output(digest, output)

    assert updated.summary == "Updated source-grounded summary"
    assert updated.important_articles[0].headline_ko == "애플 실적 핵심"
    assert updated.important_articles[0].summary_ko == "서비스 매출이 주목됩니다."
    assert updated.important_articles[0].category == "earnings"
    assert updated.additional_articles[0].headline_ko == "서비스 업데이트"
    assert updated.additional_articles[0].summary_ko == "카탈로그가 확대됐습니다."
    assert updated.additional_articles[0].category == "other"
