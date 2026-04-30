from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.parse

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatCompletionProviderRequest,
    LiveAnalysisOutput,
    LiveProviderRequest,
)
from app.features.market_data import service as market_data_service
from app.features.market_data.schemas import MarketQuote
from app.main import create_app

APPLE_NEWS_QUERY = "Apple Inc AAPL latest company news earnings official business controversy"


class NewsIntentSummaryProvider:
    def __init__(self) -> None:
        self.intent_requests: List[Any] = []
        self.completion_requests: List[ChatCompletionProviderRequest] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return {
            "intent": "news_digest",
            "stock_query": "AAPL",
            "market": "US",
            "horizon_type": None,
            "analysis_mode": None,
            "source_hints": ["google news"],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def complete_chat(self, request: ChatCompletionProviderRequest) -> str:
        self.completion_requests.append(request)
        return "LLM 요약: 애플 뉴스의 핵심은 실적, AI 전략, 공급망 이슈입니다."

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        raise AssertionError("News digest requests must not run stock analysis.")


class JsonNewsSummaryProvider(NewsIntentSummaryProvider):
    def complete_chat(self, request: ChatCompletionProviderRequest) -> str:
        self.completion_requests.append(request)
        first_article_id = request.messages[-1]["content"].split('"id": "')[1].split('"')[0]
        return """
        {{
          "summary": "2026년 4월 30일 기준 Apple Inc (AAPL) 주요 뉴스입니다.",
          "articles": [
            {{
              "id": "{article_id}",
              "headline_ko": "오늘 Q2 2026 실적 발표 예정",
              "summary_ko": "애플은 장 마감 후 실적 컨퍼런스콜을 진행합니다.",
              "category": "earnings"
            }}
          ]
        }}
        """.format(article_id=first_article_id)


def _save_openai_credential(client: TestClient, raw_key: str) -> None:
    response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": raw_key,
        },
    )
    assert response.status_code == 200


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
        as_of_at="2026-04-29T16:00:00-04:00",
        source="serpapi_google_finance",
    )


def _request_query_from_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query_items = urllib.parse.parse_qs(parsed.query)
    return query_items.get("q", query_items.get("query", [""]))[0]


def _tavily_results_for_query(query: str) -> List[Dict[str, Any]]:
    lower_query = query.lower()
    if "product launch" in lower_query or "ai strategy" in lower_query:
        return [
            {
                "title": "Apple previews new AI features across iPhone and services",
                "url": "https://example.com/apple-ai-product",
                "content": "Apple is expected to expand Apple Intelligence and service features.",
                "published_date": "2026-04-29T12:30:00-04:00",
                "score": 0.88,
            }
        ]
    if "ceo leadership" in lower_query or "executive succession" in lower_query:
        return [
            {
                "title": "Apple leadership succession questions remain in focus",
                "url": "https://example.com/apple-leadership",
                "content": "Investors are monitoring executive succession and governance signals.",
                "published_date": "2026-04-28T17:00:00-04:00",
                "score": 0.82,
            }
        ]
    if "regulation lawsuit" in lower_query or "antitrust" in lower_query:
        return [
            {
                "title": "Apple faces renewed App Store antitrust scrutiny",
                "url": "https://example.com/apple-antitrust",
                "content": "Regulators are reviewing App Store rules and platform fees.",
                "published_date": "2026-04-29T08:00:00-04:00",
                "score": 0.84,
            }
        ]
    if "spglobal.com/market-intelligence" in lower_query:
        return [
            {
                "title": "Apple earnings preview weighs valuation and Visible Alpha consensus",
                "url": "https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/04/apple-earnings-preview-q2-2026",
                "content": "Analysts are focused on valuation, consensus estimates, and guidance risk.",
                "published_date": "2026-04-29T07:30:00-04:00",
                "score": 0.9,
            }
        ]
    if "analyst target" in lower_query:
        return [
            {
                "title": "Wall Street analysts review Apple valuation targets",
                "url": "https://example.com/apple-valuation-targets",
                "content": "Analysts are comparing price targets, valuation, and guidance risk.",
                "published_date": "2026-04-29T07:45:00-04:00",
                "score": 0.86,
            }
        ]
    return [
        {
            "title": "Apple earnings preview highlights services growth",
            "url": "https://example.com/apple-earnings?utm_source=tavily",
            "content": "Investors are watching services, iPhone demand, and AI spending.",
            "published_date": "2026-04-29T13:00:00-04:00",
            "score": 0.92,
        },
        {
            "title": "Analysts debate Apple AI roadmap",
            "url": "https://example.com/apple-ai",
            "content": "Analysts are focused on Apple Intelligence and device upgrades.",
            "published_date": "2026-04-29T09:00:00-04:00",
            "score": 0.86,
        },
    ]


def _news_payload_for_url(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    _ = headers, timeout_seconds
    if payload is not None:
        query = str(payload["query"])
        assert "Apple Inc AAPL" in query
        return {"results": _tavily_results_for_query(query)}
    if "gnews.io" in url:
        assert "Apple+Inc+AAPL" in url or "Apple%20Inc%20AAPL" in url
        return {
            "articles": [
                {
                    "title": "Apple earnings preview highlights services growth",
                    "url": "https://example.com/apple-earnings",
                    "description": "Duplicate URL should be merged into the Tavily result.",
                    "publishedAt": "2026-04-29T13:05:00-04:00",
                    "source": {"name": "GNews Markets"},
                },
                {
                    "title": "Apple supply chain checks improve before results",
                    "url": "https://example.com/apple-supply-chain",
                    "description": "Supplier checks point to resilient demand.",
                    "publishedAt": "2026-04-28T21:00:00-04:00",
                    "source": {"name": "GNews Markets"},
                },
            ]
        }
    if "engine=google_news" in url:
        query = _request_query_from_url(url)
        assert "Apple Inc AAPL" in query
        return {
            "news_results": [
                {
                    "title": "Apple announces new environmental targets",
                    "source": {"name": "Serp News"},
                    "date": "Apr 29 2026, 02:30 PM UTC-04:00",
                    "link": "https://example.com/apple-environment",
                    "snippet": "Apple described new material and battery recycling goals.",
                },
                {
                    "title": "Apple services momentum remains in focus",
                    "stories": [
                        {
                            "title": "Apple services momentum remains in focus",
                            "source": "Serp News",
                            "date": "Apr 28 2026, 06:10 PM UTC-04:00",
                            "link": "https://example.com/apple-services",
                            "snippet": "Services growth remains a central investor topic.",
                        }
                    ],
                },
            ]
        }
    if "engine=google" in url:
        query = _request_query_from_url(url)
        assert "Apple Inc AAPL" in query
        return {
            "organic_results": [
                {
                    "title": "Apple board transition draws attention",
                    "link": "https://example.com/apple-board",
                    "source": "Example Search",
                    "date": "Apr 28, 2026",
                    "snippet": "Investors are tracking leadership and governance changes.",
                },
                {
                    "title": "Apple Arcade expands game catalog",
                    "link": "https://example.com/apple-arcade",
                    "source": "Example Search",
                    "date": "Apr 27, 2026",
                    "snippet": "Apple added titles to its services catalog.",
                },
            ]
        }
    raise AssertionError(f"Unexpected news URL: {url}")


def test_news_digest_collects_providers_dedupes_and_tracks_transparency(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase064")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-phase064")
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase064")
    monkeypatch.setattr(news_digest_service, "_fetch_json", _news_payload_for_url)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스 가져와줘",
        language="ko",
    )
    expected_queries = news_digest_service._build_news_queries(
        _apple_quote(),
        "애플 뉴스 가져와줘",
    )
    provider_names = {run.provider for run in digest.provider_runs}
    provider_queries = {run.query for run in digest.provider_runs}
    all_articles = digest.important_articles + digest.additional_articles

    assert digest.status == "completed"
    assert digest.query == APPLE_NEWS_QUERY
    assert len(digest.important_articles) == 5
    assert len(digest.additional_articles) >= 2
    assert provider_names == {
        "tavily_news",
        "gnews_news",
        "serpapi_google_news",
        "serpapi_google_web",
    }
    assert provider_queries == set(expected_queries)
    assert len(digest.provider_runs) == 4 * len(expected_queries)
    assert all(run.status == "completed" for run in digest.provider_runs)
    urls = [article.url for article in all_articles]
    assert "https://example.com/apple-earnings" in urls
    assert urls.count("https://example.com/apple-earnings") == 1
    assert any(article.provider == "tavily_news" for article in digest.important_articles)
    assert any("product launch service AI strategy" in article.query for article in all_articles)
    assert any("CEO leadership executive succession" in article.query for article in all_articles)
    assert any("regulation lawsuit antitrust App Store controversy" in article.query for article in all_articles)
    assert any("site:spglobal.com/market-intelligence" in article.query for article in all_articles)
    assert "최신 뉴스" in digest.summary


def test_news_digest_prioritizes_official_earnings_and_business_news_over_quote_pages() -> None:
    from app.features.news_digest import service as news_digest_service

    articles = [
        news_digest_service._article(
            provider="tavily_news",
            query="Apple Inc AAPL latest company news earnings official business controversy",
            rank=0,
            title="Apple Inc. (AAPL) Stock Price, News, Quote & History - Yahoo Finance",
            url="https://finance.yahoo.com/quote/AAPL",
            source="Yahoo Finance",
            snippet=(
                "(AAPL) Stock Price, News, Quote & History - Yahoo Finance. ### News. "
                "My Portfolio. Markets. Stocks. Earnings. Tech. " * 20
            ),
        ),
        news_digest_service._article(
            provider="serpapi_google_web",
            query="Apple Inc AAPL latest company news earnings official business controversy",
            rank=1,
            title="Apple reports second quarter results",
            url="https://www.apple.com/newsroom/2026/04/apple-reports-second-quarter-results/",
            source="Apple Newsroom",
            published_at="2026-04-30T17:00:00-04:00",
            snippet="Apple reported quarterly revenue and services growth.",
        ),
        news_digest_service._article(
            provider="gnews_news",
            query="Apple Inc AAPL latest company news earnings official business controversy",
            rank=2,
            title="Regulators open new App Store investigation into Apple",
            url="https://example.com/apple-regulatory-risk",
            source="Market Wire",
            published_at="2026-04-29T12:00:00-04:00",
            snippet="A regulator opened a new investigation into Apple App Store rules.",
        ),
    ]

    ranked = news_digest_service._rank_articles(
        [article for article in articles if article is not None]
    )

    assert ranked[0].category == "earnings"
    assert ranked[0].importance_score > ranked[-1].importance_score
    assert ranked[0].headline_ko == "Apple reports second quarter results"
    assert ranked[0].summary_ko == "Apple reported quarterly revenue and services growth."
    assert ranked[-1].url == "https://finance.yahoo.com/quote/AAPL"
    assert ranked[-1].category == "quote_page"
    assert ranked[-1].importance_score < 0
    assert ranked[-1].snippet is not None
    assert len(ranked[-1].snippet) <= 260


def test_news_digest_query_targets_news_instead_of_stock_price_pages() -> None:
    from app.features.news_digest import service as news_digest_service

    query = news_digest_service._build_news_query(
        _apple_quote(),
        "애플 뉴스 보여줘",
    )

    assert query == "Apple Inc AAPL latest company news earnings official business controversy"
    assert "stock price" not in query.lower()


def test_news_digest_builds_diversified_us_company_event_queries() -> None:
    from app.features.news_digest import service as news_digest_service

    queries = news_digest_service._build_news_queries(
        _apple_quote(),
        "애플 뉴스 보여줘",
    )

    assert queries[0] == APPLE_NEWS_QUERY
    assert any("product launch service AI strategy" in query for query in queries)
    assert any("CEO leadership executive succession" in query for query in queries)
    assert any("regulation lawsuit antitrust App Store controversy" in query for query in queries)
    assert any("analyst target valuation" in query for query in queries)
    assert any("site:spglobal.com/market-intelligence" in query for query in queries)
    assert len(set(queries)) == len(queries)


def test_news_digest_selects_diverse_important_articles() -> None:
    from app.features.news_digest import service as news_digest_service

    articles = [
        news_digest_service._article(
            provider="tavily_news",
            query=APPLE_NEWS_QUERY,
            rank=index,
            title=f"Apple reports quarterly earnings update {index}",
            url=f"https://investor.apple.com/newsroom/results-{index}",
            source="Apple Investor Relations",
            published_at=f"2026-04-29T1{index}:00:00-04:00",
            snippet="Apple reported quarterly revenue, earnings, and guidance.",
        )
        for index in range(4)
    ]
    articles.extend(
        [
            news_digest_service._article(
                provider="serpapi_google_news",
                query="Apple Inc AAPL regulation lawsuit antitrust App Store controversy",
                rank=0,
                title="Apple faces renewed App Store antitrust scrutiny",
                url="https://marketwire.example.com/apple-antitrust-risk",
                source="Market Wire",
                published_at="2026-04-29T08:00:00-04:00",
                snippet="Regulators are reviewing App Store rules and platform fees.",
            ),
            news_digest_service._article(
                provider="tavily_news",
                query="Apple Inc AAPL product launch",
                rank=0,
                title="Apple unveils new iPad product launch plans",
                url="https://productdaily.example.com/apple-ipad-launch",
                source="Product Daily",
                published_at="2026-04-29T07:00:00-04:00",
                snippet="Apple is preparing a new iPad launch and device refresh.",
            ),
            news_digest_service._article(
                provider="gnews_news",
                query="Apple Inc AAPL analyst target valuation research consensus",
                rank=0,
                title="Wall Street analyst reviews Apple valuation target",
                url="https://analystwire.example.com/apple-valuation-targets",
                source="Analyst Wire",
                published_at="2026-04-29T06:30:00-04:00",
                snippet="An analyst is comparing price target assumptions and valuation risk.",
            ),
        ]
    )

    ranked = news_digest_service._rank_articles(
        [article for article in articles if article is not None]
    )
    important = news_digest_service._select_diverse_articles(ranked, 5)
    categories = [article.category for article in important]

    assert len(important) == 5
    assert categories.count("earnings") <= 2
    assert "controversy" in categories
    assert "product_service" in categories
    assert "market_reaction" in categories


def test_news_digest_uses_naver_and_public_social_search_when_credentials_available(
    monkeypatch,
) -> None:
    from app.features.news_digest import service as news_digest_service

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        _ = payload, timeout_seconds
        if "openapi.naver.com" in url:
            assert headers is not None
            assert headers["X-Naver-Client-Id"] == "naver-client"
            assert headers["X-Naver-Client-Secret"] == "naver-secret"
            assert "애플" in _request_query_from_url(url) or "Apple" in _request_query_from_url(url)
            return {
                "items": [
                    {
                        "title": "<b>애플</b>, 국내 뉴스에서 AI 전략 주목",
                        "originallink": "https://news.example.kr/apple-ai-strategy",
                        "description": "국내 투자자들은 애플의 AI와 서비스 전략을 보고 있습니다.",
                        "pubDate": "Wed, 29 Apr 2026 18:00:00 +0900",
                    }
                ]
            }
        if "engine=google" in url:
            query = _request_query_from_url(url)
            assert "site:x.com" in query or "site:twitter.com" in query or "site:facebook.com" in query
            return {
                "organic_results": [
                    {
                        "title": "Tim Cook comments on Apple policy debate",
                        "link": "https://x.com/tim_cook/status/123",
                        "source": "X",
                        "date": "Apr 29, 2026",
                        "snippet": "Tim Cook discussed Apple, policy, and AI investment.",
                    },
                    {
                        "title": "Apple discussion mentions Trump tariff pressure",
                        "link": "https://www.facebook.com/example/posts/456",
                        "source": "Facebook",
                        "date": "Apr 29, 2026",
                        "snippet": "Public posts discussed Trump, tariffs, and Apple supply chain exposure.",
                    },
                ]
            }
        raise AssertionError(f"Unexpected news URL: {url}")

    monkeypatch.setenv("NAVER_CLIENT_ID", "naver-client")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "naver-secret")
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-social")
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    digest = news_digest_service.create_news_digest(
        _apple_quote(),
        requested_query="애플 뉴스와 팀쿡 트럼프 SNS 반응",
        language="ko",
        providers=("naver_news", "serpapi_social_web"),
    )

    providers = {run.provider for run in digest.provider_runs}
    article_providers = {article.provider for article in digest.important_articles}
    serialized = digest.model_dump_json()

    assert digest.status == "completed"
    assert providers == {"naver_news", "serpapi_social_web"}
    assert {"naver_news", "serpapi_social_web"}.issubset(article_providers)
    assert any(article.source_domain == "x.com" for article in digest.important_articles)
    assert any(article.source_domain == "news.example.kr" for article in digest.important_articles)
    assert "naver-secret" not in serialized
    assert "serpapi-social" not in serialized


def test_korean_news_request_returns_digest_without_horizon_and_uses_llm_summary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.features.news_digest import service as news_digest_service

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase067")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-phase067")
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase067")
    monkeypatch.setattr(news_digest_service, "_fetch_json", _news_payload_for_url)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": _apple_quote() if symbol == "AAPL" else None,
        raising=False,
    )

    provider = NewsIntentSummaryProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, "sk-news-digest-secret")

    response = client.post(
        "/conversations",
        json={
            "content": "애플 뉴스 가져와줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "news_digest"
    assert body["missing_inputs"] == []
    assert body["analysis_request"] is None
    assert body["news_digest"]["symbol"] == "AAPL"
    assert body["news_digest"]["summary"].startswith("LLM 요약")
    assert body["news_digest"]["important_articles"][0]["url"].startswith("https://example.com/")
    assert body["messages"][-1]["news_digest"]["provider_runs"][0]["provider"] == "tavily_news"
    assert body["messages"][-1]["meta"] == "뉴스 요약"
    assert provider.completion_requests
    assert provider.analysis_requests == []
    assert "sk-news-digest-secret" not in response.text


def test_korean_news_typo_routes_to_news_digest_without_llm_intent(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.features.news_digest import service as news_digest_service

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase083")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-phase083")
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase083")
    monkeypatch.setattr(news_digest_service, "_fetch_json", _news_payload_for_url)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": _apple_quote() if symbol == "AAPL" else None,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "애플 뉴ㅛㅡ",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "news_digest"
    assert body["missing_inputs"] == []
    assert body["analysis_request"] is None
    assert body["news_digest"]["symbol"] == "AAPL"
    assert body["messages"][-1]["meta"] == "뉴스 요약"
    assert body["messages"][-1]["news_digest"]["important_articles"]


def test_llm_news_json_updates_korean_article_headlines(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.features.news_digest import service as news_digest_service

    captured_digest_ids: List[str] = []

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        data = _news_payload_for_url(
            url,
            headers=headers,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        return data

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase074")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-phase074")
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase074")
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": _apple_quote() if symbol == "AAPL" else None,
        raising=False,
    )

    provider = JsonNewsSummaryProvider()

    original_prompt = news_digest_service.create_news_digest

    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, "sk-news-json-secret")

    response = client.post(
        "/conversations",
        json={
            "content": "애플 뉴스 가져와줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert original_prompt is news_digest_service.create_news_digest
    body = response.json()
    first_article = body["news_digest"]["important_articles"][0]
    captured_digest_ids.append(first_article["id"])
    assert body["news_digest"]["summary"] == "2026년 4월 30일 기준 Apple Inc (AAPL) 주요 뉴스입니다."
    assert first_article["headline_ko"] == "오늘 Q2 2026 실적 발표 예정"
    assert first_article["summary_ko"] == "애플은 장 마감 후 실적 컨퍼런스콜을 진행합니다."
    assert first_article["category"] == "earnings"
    prompt_text = str(provider.completion_requests[0].messages)
    assert "Return compact JSON" in prompt_text
