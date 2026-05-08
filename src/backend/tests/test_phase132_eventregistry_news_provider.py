from typing import Any, Dict, Optional

from app.features.market_data.schemas import MarketQuote


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


def test_eventregistry_provider_posts_recent_article_query_and_normalizes_results(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    captured_payloads: list[Dict[str, Any]] = []
    monkeypatch.setenv("EVENTREGISTRY_API_KEY", "eventregistry-phase132-secret")

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        assert url == "https://www.eventregistry.org/api/v1/article"
        assert headers is not None
        assert timeout_seconds > 0
        assert payload is not None
        captured_payloads.append(payload)
        return {
            "articles": {
                "results": [
                    {
                        "title": "Apple services revenue grows as AI rollout remains in focus",
                        "url": "https://example.com/apple-services-ai?utm_source=eventregistry",
                        "source": {"title": "Reuters"},
                        "dateTimePub": "2026-05-06T13:00:00Z",
                        "body": "Apple services revenue and Apple Intelligence timing were the main investor focus.",
                        "sentiment": 0.21,
                    }
                ]
            }
        }

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=("eventregistry_news",),
        provider_limit=3,
        query_limit=1,
    )

    assert digest.status == "completed"
    assert len(captured_payloads) == 1
    payload = captured_payloads[0]
    assert payload["apiKey"] == "eventregistry-phase132-secret"
    assert payload["action"] == "getArticles"
    assert payload["keyword"] == "Apple Inc AAPL latest company news earnings official business controversy"
    assert payload["dateEnd"] == "2026-05-06"
    assert payload["forceMaxDataTimeWindow"] == 31
    assert payload["articlesCount"] == 3
    article = digest.important_articles[0]
    assert article.provider == "eventregistry_news"
    assert article.title == "Apple services revenue grows as AI rollout remains in focus"
    assert article.url == "https://example.com/apple-services-ai"
    assert article.source == "Reuters"
    assert article.published_at == "2026-05-06T13:00:00+00:00"
    assert "eventregistry-phase132-secret" not in digest.model_dump_json()


def test_eventregistry_provider_missing_key_is_reported_as_missing_credential(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    monkeypatch.delenv("EVENTREGISTRY_API_KEY", raising=False)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=("eventregistry_news",),
        provider_limit=3,
        query_limit=1,
    )

    assert digest.status == "empty"
    assert len(digest.provider_runs) == 1
    assert digest.provider_runs[0].provider == "eventregistry_news"
    assert digest.provider_runs[0].status == "missing_credential"
    assert digest.provider_runs[0].result_count == 0


def test_eventregistry_provider_malformed_payload_is_reported_as_provider_error(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    monkeypatch.setenv("EVENTREGISTRY_API_KEY", "eventregistry-phase140-secret")

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        _ = url, headers, payload, timeout_seconds
        return {"articles": {"results": None}}

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=("eventregistry_news",),
        provider_limit=3,
        query_limit=1,
    )

    assert digest.status == "empty"
    assert digest.warnings == ["provider_error:eventregistry_news"]
    assert len(digest.provider_runs) == 1
    assert digest.provider_runs[0].provider == "eventregistry_news"
    assert digest.provider_runs[0].status == "provider_error"
    assert digest.provider_runs[0].result_count == 0
