from app.features.analysis.schemas import (
    AnalysisResponse,
    EvidenceItem,
    SourceAuditSummary,
)
from app.features.conversations import service as conversation_service
from app.features.market_data.schemas import MarketQuote
from app.features.news_digest.schemas import NewsArticle, NewsDigest, NewsSearchRun
from app.features.scoring.schemas import ScoreDriver, ScoreResponse


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


def _article(
    title: str,
    *,
    provider: str,
    category: str,
    source: str,
    url: str,
) -> NewsArticle:
    return NewsArticle(
        id=f"news_{provider}_{category}",
        title=title,
        url=url,
        source=source,
        published_at="2026-05-06T13:00:00+00:00",
        snippet=f"{title} summary.",
        provider=provider,
        query="Apple Inc AAPL latest company news earnings official business controversy",
        rank=0,
        category=category,
        headline_ko=title,
        summary_ko=None,
        importance_score=80.0,
        source_domain=url.split("/")[2],
    )


def test_news_digest_reply_groups_real_headlines_with_sources_and_as_of_at() -> None:
    digest = NewsDigest(
        digest_id="digest_phase134",
        status="completed",
        market="US",
        symbol="AAPL",
        stock_name="Apple Inc",
        query="Apple Inc AAPL latest company news earnings official business controversy",
        generated_at="2026-05-06T20:00:00Z",
        summary="Apple news summary.",
        key_points=[],
        important_articles=[
            _article(
                "Apple services revenue hits a new high",
                provider="yahoo_finance_rss",
                category="earnings",
                source="Yahoo Finance",
                url="https://finance.yahoo.com/news/apple-services-record",
            ),
            _article(
                "Apple faces fresh App Store antitrust questions",
                provider="google_news_rss",
                category="controversy",
                source="Market Wire",
                url="https://example.com/apple-antitrust",
            ),
            _article(
                "Reddit investors discuss Apple AI timing",
                provider="reddit_public_search",
                category="market_reaction",
                source="r/stocks",
                url="https://www.reddit.com/r/stocks/comments/apple_ai/",
            ),
        ],
        additional_articles=[],
        provider_runs=[
            NewsSearchRun(
                provider="yahoo_finance_rss",
                query="AAPL",
                result_count=1,
                status="completed",
            )
        ],
        warnings=[],
    )

    message = conversation_service._news_digest_reply(_apple_quote(), digest, "ko")

    assert "2026-05-06T16:00:00-04:00 기준" in message.content
    assert "실적·가이던스" in message.content
    assert "규제·소송" in message.content
    assert "커뮤니티·시장 반응" in message.content
    assert "[Apple services revenue hits a new high](https://finance.yahoo.com/news/apple-services-record)" in message.content
    assert "Yahoo Finance · yahoo_finance_rss" in message.content
    assert "[Reddit investors discuss Apple AI timing](https://www.reddit.com/r/stocks/comments/apple_ai)" in message.content


def test_scenario_prediction_copy_includes_as_of_at_and_not_advice_label() -> None:
    analysis = AnalysisResponse(
        analysis_request_id="analysis_phase134",
        status="completed",
        market="US",
        symbol="AAPL",
        stock_name="Apple Inc",
        horizon_type="swing",
        analysis_mode="quick",
        as_of_at="2026-05-06T16:00:00-04:00",
        included_document_count=2,
        excluded_document_count=0,
        source_audit=SourceAuditSummary(prompt_document_ids=["src_1", "src_2"]),
        source_documents=[],
        evidence_items=[
            EvidenceItem(
                source_document_id="src_1",
                stance="bullish",
                weight=0.7,
                summary="Services growth remains resilient",
                quote_excerpt="services growth",
            ),
            EvidenceItem(
                source_document_id="src_2",
                stance="bearish",
                weight=0.4,
                summary="AI Siri delays pressure confidence",
                quote_excerpt="AI delays",
            ),
        ],
        summary="Apple source-grounded analysis.",
        score_result=ScoreResponse(
            score_id="score_phase134",
            analysis_request_id="analysis_phase134",
            status="scored",
            buy_probability=38.0,
            hold_probability=44.0,
            sell_probability=18.0,
            confidence_score=0.62,
            expected_return_min_pct=-4.0,
            expected_return_max_pct=8.0,
            downside_probability=24.0,
            similar_event_sample_count=12,
            similar_event_win_rate=58.0,
            similar_event_median_return_pct=2.5,
            drivers=[
                ScoreDriver(
                    source_document_id="src_1",
                    stance="bullish",
                    weight=0.7,
                    probability_impact="supports_buy",
                    summary="Services growth remains resilient",
                )
            ],
            rationale="Scored from evidence.",
        ),
    )

    content = conversation_service._analysis_message_content(analysis, "swing", "ko")

    assert "기준 시각: 2026-05-06T16:00:00-04:00" in content
    assert "정보 기반 시나리오 분석" in content
    assert "기준 시나리오" in content
    assert "강세 시나리오" in content
    assert "약세 시나리오" in content
    assert "투자 조언이 아니라" in content
