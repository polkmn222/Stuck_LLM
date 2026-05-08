from pathlib import Path
from typing import Dict, Optional

from app.features.market_data.schemas import MarketQuote
from app.shared.state_store import LocalStateStore


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


def _rss(title: str, link: str, source: str, pub_date: str) -> str:
    return f"""
    <rss version="2.0">
      <channel>
        <item>
          <title><![CDATA[{title}]]></title>
          <link>{link}</link>
          <source>{source}</source>
          <pubDate>{pub_date}</pubDate>
          <description><![CDATA[{title} summary with Apple services and AI.]]></description>
        </item>
      </channel>
    </rss>
    """


def test_free_rss_providers_collect_headlines_and_use_provider_cache(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.features.news_digest import service as news_digest_service

    calls: list[str] = []

    def fake_fetch_text(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 10,
    ) -> str:
        calls.append(url)
        assert headers is not None
        assert timeout_seconds > 0
        if "seekingalpha.com" in url:
            return _rss(
                "Apple: 3 Reasons This Quarter Could Reset The Entire Story",
                "https://seekingalpha.com/article/4897069-apple-reset?utm_source=chatgpt.com",
                "Seeking Alpha",
                "Wed, 06 May 2026 14:30:00 GMT",
            )
        if "feeds.finance.yahoo.com" in url:
            return _rss(
                "Apple services revenue hits a new high",
                "https://finance.yahoo.com/news/apple-services-record",
                "Yahoo Finance",
                "Wed, 06 May 2026 13:20:00 GMT",
            )
        if "news.google.com/rss" in url:
            return _rss(
                "Apple faces fresh App Store antitrust questions",
                "https://example.com/apple-antitrust",
                "Market Wire",
                "Wed, 06 May 2026 12:10:00 GMT",
            )
        if "bing.com/news/search" in url:
            return _rss(
                "Apple suppliers prepare for iPhone demand cycle",
                "https://example.com/apple-supply-chain",
                "Bing News",
                "Wed, 06 May 2026 11:00:00 GMT",
            )
        raise AssertionError(f"Unexpected RSS URL: {url}")

    monkeypatch.setattr(news_digest_service, "_fetch_text", fake_fetch_text, raising=False)
    store = LocalStateStore(tmp_path / "state.json")
    providers = (
        "seekingalpha_rss",
        "yahoo_finance_rss",
        "google_news_rss",
        "bing_news_rss",
    )

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=providers,
        provider_limit=2,
        query_limit=1,
        store=store,
    )
    cached_digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=providers,
        provider_limit=2,
        query_limit=1,
        store=store,
    )

    all_titles = {
        article.title
        for article in digest.important_articles + digest.additional_articles
    }
    assert digest.status == "completed"
    assert {run.provider for run in digest.provider_runs} == set(providers)
    assert all(run.status == "completed" for run in digest.provider_runs)
    assert "Apple: 3 Reasons This Quarter Could Reset The Entire Story" in all_titles
    assert "Apple services revenue hits a new high" in all_titles
    assert "Apple faces fresh App Store antitrust questions" in all_titles
    assert "Apple suppliers prepare for iPhone demand cycle" in all_titles
    assert any(
        article.url == "https://seekingalpha.com/article/4897069-apple-reset"
        for article in digest.important_articles + digest.additional_articles
    )
    assert len(calls) == len(providers)
    assert len(cached_digest.provider_runs) == len(providers)


def test_default_news_digest_uses_free_rss_when_no_paid_news_keys(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    for env_name in (
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
        "SERPAPI_API_KEY",
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
        _ = headers, timeout_seconds
        return _rss(
            "Apple headline from free RSS",
            "https://example.com/apple-free-rss",
            "Free RSS",
            "Wed, 06 May 2026 10:00:00 GMT",
        )

    def unexpected_fetch_json(*args, **kwargs):
        raise AssertionError("Default no-key news path should not call paid JSON providers.")

    monkeypatch.setattr(news_digest_service, "_fetch_text", fake_fetch_text, raising=False)
    monkeypatch.setattr(news_digest_service, "_fetch_json", unexpected_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스",
        language="ko",
        provider_limit=1,
        query_limit=1,
    )

    assert digest.status == "completed"
    assert {run.provider for run in digest.provider_runs} == {
        "seekingalpha_rss",
        "yahoo_finance_rss",
        "google_news_rss",
        "bing_news_rss",
    }
    assert all(run.status == "completed" for run in digest.provider_runs)
    assert digest.important_articles[0].title == "Apple headline from free RSS"
