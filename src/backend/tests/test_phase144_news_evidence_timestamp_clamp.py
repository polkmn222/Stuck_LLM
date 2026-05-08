from typing import Optional

from app.features.market_data.schemas import MarketQuote
from app.features.news_digest.schemas import NewsArticle, NewsDigest


def _apple_quote() -> MarketQuote:
    return MarketQuote(
        market="US",
        symbol="AAPL",
        name="Apple Inc",
        exchange="NASDAQ",
        currency="USD",
        last_price=270.71,
        previous_close=267.56,
        change_pct=1.18,
        as_of_at="2026-05-06T16:00:00-04:00",
        source="serpapi_google_finance",
    )


def _digest(*, article_published_at: Optional[str], generated_at: str) -> NewsDigest:
    return NewsDigest(
        digest_id="digest_phase144",
        status="completed",
        market="US",
        symbol="AAPL",
        stock_name="Apple Inc",
        query="Apple Inc AAPL latest company news",
        generated_at=generated_at,
        summary="Apple news digest.",
        key_points=[],
        important_articles=[
            NewsArticle(
                id="article_phase144",
                title="Apple article without a source timestamp",
                url="https://example.com/apple-source",
                source="Example News",
                published_at=article_published_at,
                snippet="Apple source snippet.",
                provider="eventregistry_news",
                query="Apple Inc AAPL latest company news",
                rank=0,
                category="core_business",
                importance_score=75.0,
            )
        ],
        additional_articles=[],
        provider_runs=[],
        warnings=[],
    )


def test_missing_news_article_date_falls_back_no_later_than_quote_as_of() -> None:
    from app.features.conversations import service as conversation_service

    documents = conversation_service._news_digest_source_documents(
        _digest(
            article_published_at=None,
            generated_at="2026-05-07T09:00:00+00:00",
        ),
        _apple_quote(),
    )

    assert len(documents) == 1
    assert documents[0].published_at == "2026-05-06T16:00:00-04:00"
    assert "timestamp_clamped_to_quote_as_of" in documents[0].safety_flags


def test_actual_future_news_article_date_remains_excludable() -> None:
    from app.features.conversations import service as conversation_service

    documents = conversation_service._news_digest_source_documents(
        _digest(
            article_published_at="2026-05-07T09:00:00+00:00",
            generated_at="2026-05-07T09:05:00+00:00",
        ),
        _apple_quote(),
    )

    assert len(documents) == 1
    assert documents[0].published_at == "2026-05-07T09:00:00+00:00"
    assert "timestamp_clamped_to_quote_as_of" not in documents[0].safety_flags
