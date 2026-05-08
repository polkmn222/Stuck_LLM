import urllib.parse
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


def _reddit_payload(*titles: str, subreddit: str = "stocks") -> Dict[str, object]:
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "title": title,
                        "permalink": f"/r/{subreddit}/comments/{index}/apple_stock/",
                        "subreddit_name_prefixed": f"r/{subreddit}",
                        "selftext": f"{title} discussion body",
                        "created_utc": 1778068800 + index,
                    }
                }
                for index, title in enumerate(titles)
            ]
        }
    }


def test_reddit_public_search_provider_searches_stock_subreddits_and_dedupes(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    urls: list[str] = []

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        assert "old.reddit.com/r/" in url
        assert "search.json" in url
        assert "Apple+Inc+AAPL" in url or "Apple%20Inc%20AAPL" in url
        assert headers is not None
        assert payload is None
        assert timeout_seconds > 0
        urls.append(url)
        if "/r/stocks/" in url:
            return _reddit_payload(
                "Apple stock holders debate AI execution risk",
                "Apple services growth thread",
            )
        return _reddit_payload(
            "Apple stock holders debate AI execution risk",
            "Apple valuation looks stretched to some retail investors",
            subreddit="investing",
        )

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="apple stock reddit discussion",
        language="en",
        providers=("reddit_public_search",),
        provider_limit=3,
        query_limit=1,
    )

    titles = {
        article.title
        for article in digest.important_articles + digest.additional_articles
    }
    assert digest.status == "completed"
    assert len(urls) >= 2
    assert len(digest.provider_runs) == 1
    assert digest.provider_runs[0].provider == "reddit_public_search"
    assert digest.provider_runs[0].status == "completed"
    assert "Apple stock holders debate AI execution risk" in titles
    assert "Apple services growth thread" in titles
    assert "Apple valuation looks stretched to some retail investors" in titles
    assert sum(1 for article in digest.important_articles if article.provider == "reddit_public_search") >= 1


def test_default_reddit_request_adds_public_search_without_paid_news_keys(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    for env_name in (
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
        "SERPAPI_API_KEY",
        "EVENTREGISTRY_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ):
        monkeypatch.delenv(env_name, raising=False)

    def fake_fetch_text(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 10,
    ) -> str:
        _ = url, headers, timeout_seconds
        return """
        <rss version="2.0"><channel><item>
          <title>Apple headline from free RSS</title>
          <link>https://example.com/apple-free-rss</link>
          <source>Free RSS</source>
          <pubDate>Wed, 06 May 2026 10:00:00 GMT</pubDate>
          <description>Apple free RSS summary.</description>
        </item></channel></rss>
        """

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        _ = headers, payload, timeout_seconds
        assert "old.reddit.com/r/" in url
        return _reddit_payload("Reddit investors discuss Apple AI timing")

    monkeypatch.setattr(news_digest_service, "_fetch_text", fake_fetch_text, raising=False)
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 레딧 커뮤니티 반응",
        language="ko",
        provider_limit=1,
        query_limit=1,
    )

    providers = {run.provider for run in digest.provider_runs}
    assert "reddit_public_search" in providers
    assert "reddit_crawl" not in providers
    assert {"seekingalpha_rss", "yahoo_finance_rss", "google_news_rss", "bing_news_rss"}.issubset(
        providers
    )


def test_reddit_sentiment_request_activates_public_search_and_preserves_user_terms(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    for env_name in (
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
        "SERPAPI_API_KEY",
        "EVENTREGISTRY_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ):
        monkeypatch.delenv(env_name, raising=False)

    captured_reddit_queries: list[str] = []

    def fake_fetch_text(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 10,
    ) -> str:
        _ = url, headers, timeout_seconds
        return """
        <rss version="2.0"><channel><item>
          <title>Apple headline from free RSS</title>
          <link>https://example.com/apple-free-rss</link>
          <source>Free RSS</source>
          <pubDate>Wed, 06 May 2026 10:00:00 GMT</pubDate>
          <description>Apple free RSS summary.</description>
        </item></channel></rss>
        """

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        _ = headers, payload, timeout_seconds
        assert "old.reddit.com/r/" in url
        query = str(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["q"][0])
        captured_reddit_queries.append(query)
        return _reddit_payload("Reddit investors connect Trump tariff risk to Apple")

    monkeypatch.setattr(news_digest_service, "_fetch_text", fake_fetch_text, raising=False)
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="investor sentiment on Trump tariffs from X and social reaction",
        language="en",
        provider_limit=1,
        query_limit=1,
    )

    providers = {run.provider for run in digest.provider_runs}
    assert "reddit_public_search" in providers
    assert captured_reddit_queries
    assert any("Apple Inc AAPL" in query for query in captured_reddit_queries)
    assert any("Trump tariffs" in query for query in captured_reddit_queries)
    assert any("investor sentiment" in query for query in captured_reddit_queries)
    assert "Trump policy tariffs" not in news_digest_service.SOCIAL_QUERY_SUFFIX
    assert "public posts" in news_digest_service.SOCIAL_QUERY_SUFFIX
    assert "investor reaction" in news_digest_service.SOCIAL_QUERY_SUFFIX


def test_reddit_public_search_records_warning_when_some_subreddits_fail(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        _ = headers, payload, timeout_seconds
        if "/r/stocks/" in url:
            return _reddit_payload("Apple retail holders debate tariff pressure")
        raise news_digest_service.NewsProviderError("rate limited")

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="apple stock reddit discussion",
        language="en",
        providers=("reddit_public_search",),
        provider_limit=3,
        query_limit=1,
    )

    assert digest.status == "partial"
    assert digest.warnings == ["provider_error:reddit_public_search"]
    assert len(digest.provider_runs) == 1
    run = digest.provider_runs[0]
    assert run.provider == "reddit_public_search"
    assert run.status == "partial_provider_error"
    assert run.warning == "provider_error:reddit_public_search"
    assert run.result_count == 1
    assert digest.important_articles[0].title == "Apple retail holders debate tariff pressure"


def test_reddit_public_search_stops_after_rate_limit(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    urls: list[str] = []

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        _ = headers, payload, timeout_seconds
        urls.append(url)
        if "/r/stocks/" in url:
            return _reddit_payload("Apple retail holders debate AI rollout")
        raise news_digest_service.NewsProviderError("News provider request failed:429")

    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="apple stock reddit discussion",
        language="en",
        providers=("reddit_public_search",),
        provider_limit=3,
        query_limit=1,
    )

    assert digest.status == "partial"
    assert len(urls) == 2
    assert digest.provider_runs[0].status == "partial_provider_error"
    assert digest.provider_runs[0].result_count == 1


def test_news_provider_cache_version_is_bumped_for_phase_143_changes() -> None:
    from app.features.news_digest import service as news_digest_service

    components = news_digest_service._provider_cache_components(
        "reddit_public_search",
        "Apple Inc AAPL investor sentiment",
        3,
        _apple_quote(),
    )

    assert components["provider_version"] == "phase_143_news_provider_v2"
