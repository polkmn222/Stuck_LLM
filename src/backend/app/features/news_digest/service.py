import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.credentials.external_providers import (
    get_external_provider_credential,
    get_naver_search_credential,
)
from app.features.market_data import service as market_data_service
from app.features.market_data.schemas import MarketQuote
from app.features.news_digest.schemas import (
    NewsArticle,
    NewsCategory,
    NewsDigest,
    NewsProvider,
    NewsProviderRunStatus,
    NewsSearchRun,
    NewsSearchStatus,
)
from app.features.processing_cache.service import (
    get_cached_json,
    record_news_processing_run,
    set_cached_json,
)
from app.shared.provider_status import record_provider_warning
from app.shared.state_store import LocalStateStore

HTML_TAG_RE = re.compile(r"<[^>]+>")
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
DEFAULT_NEWS_PROVIDERS: Tuple[NewsProvider, ...] = (
    "tavily_news",
    "gnews_news",
    "serpapi_google_news",
    "serpapi_google_web",
)
OPTIONAL_NEWS_PROVIDERS: Tuple[NewsProvider, ...] = (
    "naver_news",
    "serpapi_social_web",
)
PROVIDER_PRIORITY: Dict[NewsProvider, int] = {
    "tavily_news": 0,
    "naver_news": 1,
    "gnews_news": 2,
    "serpapi_google_news": 3,
    "serpapi_google_web": 4,
    "serpapi_social_web": 5,
}
NEWS_QUERY_SUFFIX = "latest company news earnings official business controversy"
SOCIAL_QUERY_SUFFIX = (
    "(site:x.com OR site:twitter.com OR site:facebook.com) public posts CEO Trump policy tariffs"
)
NEWS_PROVIDER_CACHE_TTL_SECONDS = 15 * 60
SNIPPET_MAX_LENGTH = 260
QUOTE_PAGE_DOMAINS = (
    "finance.yahoo.com",
    "google.com",
    "www.google.com",
    "nasdaq.com",
    "marketwatch.com",
)
OFFICIAL_DOMAINS = (
    "apple.com",
    "investor.apple.com",
    "sec.gov",
)
CATEGORY_BASE_SCORES: Dict[NewsCategory, float] = {
    "earnings": 80.0,
    "official": 72.0,
    "core_business": 62.0,
    "controversy": 58.0,
    "market_reaction": 44.0,
    "product_service": 38.0,
    "other": 12.0,
    "quote_page": -80.0,
}

SYMBOL_QUERY_PROFILES: Dict[str, Tuple[str, ...]] = {
    "AAPL": (
        "iPhone services Apple Intelligence supply chain App Store",
        "China demand services margin device cycle",
    ),
    "GOOG": (
        "Search ads Google Cloud AI Gemini antitrust",
        "YouTube advertising cloud margin regulation",
    ),
    "GOOGL": (
        "Search ads Google Cloud AI Gemini antitrust",
        "YouTube advertising cloud margin regulation",
    ),
    "NVDA": (
        "GPU AI data center Blackwell chip demand supply",
        "semiconductor export controls hyperscaler capex",
    ),
    "TSLA": (
        "EV deliveries margins autonomous driving energy storage",
        "robotaxi FSD battery pricing competition",
    ),
    "WMT": (
        "consumer demand pricing margins retail traffic supply chain",
    ),
}

SECTOR_QUERY_PROFILES: Dict[str, Tuple[str, ...]] = {
    "Communication Services": (
        "advertising streaming subscribers AI content regulation",
    ),
    "Consumer Discretionary": (
        "consumer demand pricing margins deliveries product cycle",
    ),
    "Consumer Staples": (
        "pricing volume margins retailer demand supply chain",
    ),
    "Energy": (
        "oil gas production refining OPEC capex commodity prices",
    ),
    "Financials": (
        "net interest income credit losses capital markets regulation",
    ),
    "Health Care": (
        "FDA clinical trial drug pipeline reimbursement guidance",
    ),
    "Industrials": (
        "orders backlog aerospace defense supply chain capex",
    ),
    "Information Technology": (
        "AI cloud semiconductor software demand product roadmap",
    ),
    "Materials": (
        "commodity demand pricing volumes China industrial cycle",
    ),
    "Real Estate": (
        "occupancy rents cap rates financing debt maturity",
    ),
    "Utilities": (
        "rate case power demand renewables grid investment",
    ),
}


class MissingNewsCredentialError(Exception):
    pass


class NewsProviderError(Exception):
    pass


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _clean_text(value: Any) -> str:
    return " ".join(HTML_TAG_RE.sub("", html.unescape(str(value or ""))).split())


def _canonical_url(value: Any) -> Optional[str]:
    raw_url = _clean_text(value)
    if not raw_url:
        return None
    parsed = urllib.parse.urlsplit(raw_url)
    if not parsed.scheme or not parsed.netloc:
        return raw_url
    query_items = [
        (key, item_value)
        for key, item_value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    query = urllib.parse.urlencode(query_items)
    path = parsed.path.rstrip("/") or parsed.path
    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            query,
            "",
        )
    )


def _source_from_url(url: Optional[str]) -> Optional[str]:
    if url is None:
        return None
    parsed = urllib.parse.urlsplit(url)
    host = parsed.netloc.removeprefix("www.")
    return host or None


def _source_domain(url: Optional[str], source: Optional[str]) -> Optional[str]:
    domain = _source_from_url(url)
    if domain is not None:
        return domain
    cleaned_source = _clean_text(source)
    return cleaned_source.lower().replace(" ", "") or None


def _truncate_text(value: Any, max_length: int = SNIPPET_MAX_LENGTH) -> Optional[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", "", cleaned)
    cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"\s*[+*•-]\s*", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1].rstrip()}…"


def _combined_text(*values: Any) -> str:
    return " ".join(_clean_text(value).lower() for value in values if value)


def _contains_keyword(text: str, keyword: str) -> bool:
    if keyword.isascii() and re.fullmatch(r"[a-z0-9]+", keyword) and len(keyword) <= 3:
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None
    return keyword in text


def _contains_any_keyword(text: str, keywords: Iterable[str]) -> bool:
    return any(_contains_keyword(text, keyword) for keyword in keywords)


def _is_quote_page(title: str, url: Optional[str], snippet: Optional[str]) -> bool:
    domain = _source_from_url(url) or ""
    text = _combined_text(title, url, snippet)
    if "stock price" in text and ("quote" in text or "history" in text):
        return True
    if "google finance" in text or "yahoo finance" in text:
        return True
    if domain in QUOTE_PAGE_DOMAINS and "/quote/" in str(url or ""):
        return True
    if domain in {"google.com", "www.google.com"} and "/finance" in str(url or ""):
        return True
    return False


def _category_for_article(
    *,
    title: str,
    url: Optional[str],
    source: Optional[str],
    snippet: Optional[str],
) -> NewsCategory:
    text = _combined_text(title, url, source, snippet)
    domain = _source_from_url(url) or ""
    if _is_quote_page(title, url, snippet):
        return "quote_page"
    if _contains_any_keyword(text, ("earnings", "quarter", "q1", "q2", "q3", "q4")):
        return "earnings"
    if _contains_any_keyword(text, ("results", "revenue", "guidance", "conference call")):
        return "earnings"
    if domain.endswith(OFFICIAL_DOMAINS) or any(domain == item for item in OFFICIAL_DOMAINS):
        return "official"
    if _contains_any_keyword(text, ("official", "newsroom", "investor relations", "sec")):
        return "official"
    if _contains_any_keyword(
        text,
        (
            "regulator",
            "regulatory",
            "investigation",
            "probe",
            "lawsuit",
            "antitrust",
            "controversy",
            "논란",
            "규제",
        ),
    ):
        return "controversy"
    if _contains_any_keyword(text, ("ipad", "mac", "arcade", "product", "launch")):
        return "product_service"
    if _contains_any_keyword(
        text,
        (
            "ai",
            "service",
            "services",
            "iphone",
            "supply chain",
            "app store",
            "strategy",
            "business",
        ),
    ):
        return "core_business"
    if _contains_any_keyword(text, ("analyst", "wall street", "stock move", "target")):
        return "market_reaction"
    return "other"


def _importance_score(
    *,
    category: NewsCategory,
    title: str,
    url: Optional[str],
    source: Optional[str],
    snippet: Optional[str],
    provider: NewsProvider,
    rank: int,
) -> float:
    score = CATEGORY_BASE_SCORES[category]
    domain = _source_from_url(url) or ""
    text = _combined_text(title, url, source, snippet)
    if domain.endswith(OFFICIAL_DOMAINS) or any(domain == item for item in OFFICIAL_DOMAINS):
        score += 12
    if _contains_any_keyword(text, ("breaking", "exclusive", "major", "핵심", "주요")):
        score += 5
    if provider == "serpapi_google_news":
        score += 2
    if provider == "gnews_news":
        score += 1
    score -= min(rank, 10) * 0.8
    return round(score, 2)


def _normalize_published_at(value: Any) -> Optional[str]:
    text = _clean_text(value)
    if not text:
        return None
    try:
        parsed_rfc = parsedate_to_datetime(text)
        if parsed_rfc.tzinfo is not None:
            return parsed_rfc.isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed_iso = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed_iso.isoformat()
    except ValueError:
        pass
    for date_format in (
        "%b %d %Y, %I:%M:%S %p UTC%z",
        "%b %d %Y, %I:%M %p UTC%z",
        "%b %d, %Y",
        "%b %d %Y",
    ):
        try:
            return datetime.strptime(text, date_format).isoformat()
        except ValueError:
            continue
    return text


def _fetch_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    body = None
    method = "GET"
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
        method = "POST"
    request = urllib.request.Request(
        url,
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            data = json.loads(response.read().decode(charset))
    except (
        TimeoutError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        OSError,
        ValueError,
    ):
        raise NewsProviderError("News provider request failed.") from None
    if not isinstance(data, dict):
        raise NewsProviderError("News provider response was malformed.")
    return cast(Dict[str, Any], data)


def _article(
    *,
    provider: NewsProvider,
    query: str,
    rank: int,
    title: Any,
    url: Any,
    source: Any = None,
    published_at: Any = None,
    snippet: Any = None,
) -> Optional[NewsArticle]:
    clean_title = _clean_text(title)
    if not clean_title:
        return None
    canonical_url = _canonical_url(url)
    clean_source = _clean_text(source) or _source_from_url(canonical_url)
    clean_snippet = _truncate_text(snippet)
    source_domain = _source_domain(canonical_url, clean_source)
    category = _category_for_article(
        title=clean_title,
        url=canonical_url,
        source=clean_source,
        snippet=clean_snippet,
    )
    importance_score = _importance_score(
        category=category,
        title=clean_title,
        url=canonical_url,
        source=clean_source,
        snippet=clean_snippet,
        provider=provider,
        rank=rank,
    )
    return NewsArticle(
        id=f"news_{uuid4().hex}",
        title=clean_title,
        url=canonical_url,
        source=clean_source,
        published_at=_normalize_published_at(published_at),
        snippet=clean_snippet,
        provider=provider,
        query=query,
        rank=rank,
        category=category,
        headline_ko=clean_title,
        summary_ko=clean_snippet,
        importance_score=importance_score,
        source_domain=source_domain,
    )


def _build_news_query(quote: MarketQuote, requested_query: str) -> str:
    if quote.market == "US":
        return f"{quote.name} {quote.symbol} {NEWS_QUERY_SUFFIX}"
    cleaned_request = _clean_text(requested_query)
    if cleaned_request:
        return f"{quote.name} {quote.symbol} {cleaned_request}"
    return f"{quote.name} {quote.symbol} {NEWS_QUERY_SUFFIX}"


def _dedupe_queries(queries: Iterable[str]) -> Tuple[str, ...]:
    deduped: List[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = " ".join(query.split())
        if not normalized:
            continue
        comparable = normalized.lower()
        if comparable in seen:
            continue
        seen.add(comparable)
        deduped.append(normalized)
    return tuple(deduped)


def _build_news_queries(quote: MarketQuote, requested_query: str) -> Tuple[str, ...]:
    primary_query = _build_news_query(quote, requested_query)
    if quote.market != "US":
        cleaned_request = _clean_text(requested_query)
        return _dedupe_queries(
            (
                primary_query,
                f"{quote.name} {quote.symbol} 실적 가이던스 최신 뉴스",
                f"{quote.name} {quote.symbol} 신제품 서비스 AI 전략",
                f"{quote.name} {quote.symbol} 경영진 CEO 이슈",
                f"{quote.name} {quote.symbol} 규제 소송 논란",
                cleaned_request,
            )
        )
    company = f"{quote.name} {quote.symbol}"
    sp500_company = market_data_service.get_sp500_company(quote.symbol)
    symbol_queries = SYMBOL_QUERY_PROFILES.get(quote.symbol.upper(), ())
    sector_queries = (
        SECTOR_QUERY_PROFILES.get(sp500_company.sector, ())
        if sp500_company is not None
        else ()
    )
    return _dedupe_queries(
        (
            primary_query,
            *[f"{company} {query}" for query in symbol_queries],
            *[f"{company} {query}" for query in sector_queries],
            f"{company} product launch service AI strategy",
            f"{company} CEO leadership executive succession",
            f"{company} regulation lawsuit antitrust controversy",
            f"{company} analyst target valuation research consensus",
            f"site:spglobal.com/market-intelligence {company} earnings preview Visible Alpha",
        )
    )


def _social_source_requested(requested_query: str) -> bool:
    text = _combined_text(requested_query)
    return _contains_any_keyword(
        text,
        (
            "sns",
            "social",
            "x",
            "twitter",
            "facebook",
            "트위터",
            "페이스북",
            "트럼프",
            "trump",
            "ceo",
            "팀쿡",
            "cook",
        ),
    )


def _expand_default_providers(
    providers: Tuple[NewsProvider, ...],
    requested_query: str,
) -> Tuple[NewsProvider, ...]:
    if providers != DEFAULT_NEWS_PROVIDERS:
        return providers
    expanded: List[NewsProvider] = list(providers)
    if get_naver_search_credential() is not None:
        expanded.append("naver_news")
    if (
        get_external_provider_credential("serpapi") is not None
        and _social_source_requested(requested_query)
    ):
        expanded.append("serpapi_social_web")
    return _dedupe_providers(expanded)


def _dedupe_providers(providers: Iterable[NewsProvider]) -> Tuple[NewsProvider, ...]:
    deduped: List[NewsProvider] = []
    seen: set[NewsProvider] = set()
    for provider in providers:
        if provider in seen:
            continue
        seen.add(provider)
        deduped.append(provider)
    return tuple(deduped)


def _provider_queries(
    provider: NewsProvider,
    queries: Tuple[str, ...],
    *,
    quote: MarketQuote,
    requested_query: str,
) -> Tuple[str, ...]:
    if provider != "serpapi_social_web":
        return queries
    requested = _clean_text(requested_query)
    company = f"{quote.name} {quote.symbol}"
    return _dedupe_queries(
        (
            f"{company} {SOCIAL_QUERY_SUFFIX}",
            f"{company} {requested} {SOCIAL_QUERY_SUFFIX}",
        )
    )


def _collect_tavily_news(query: str, limit: int) -> List[NewsArticle]:
    credential = get_external_provider_credential("tavily")
    if credential is None:
        raise MissingNewsCredentialError
    payload = _fetch_json(
        "https://api.tavily.com/search",
        payload={
            "api_key": credential.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
        },
    )
    articles: List[NewsArticle] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("results", []))[:limit]):
        if not isinstance(item, dict):
            continue
        article = _article(
            provider="tavily_news",
            query=query,
            rank=index,
            title=item.get("title"),
            url=item.get("url"),
            source=item.get("source"),
            published_at=item.get("published_date") or item.get("publishedAt"),
            snippet=item.get("content") or item.get("snippet"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _collect_naver_news(query: str, limit: int) -> List[NewsArticle]:
    credential = get_naver_search_credential()
    if credential is None:
        raise MissingNewsCredentialError
    encoded_query = urllib.parse.urlencode(
        {
            "query": query,
            "display": str(limit),
            "sort": "date",
        }
    )
    payload = _fetch_json(
        f"https://openapi.naver.com/v1/search/news.json?{encoded_query}",
        headers={
            "X-Naver-Client-Id": credential.client_id,
            "X-Naver-Client-Secret": credential.client_secret,
        },
    )
    articles: List[NewsArticle] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("items", []))[:limit]):
        if not isinstance(item, dict):
            continue
        article = _article(
            provider="naver_news",
            query=query,
            rank=index,
            title=item.get("title"),
            url=item.get("originallink") or item.get("link"),
            source="Naver News",
            published_at=item.get("pubDate"),
            snippet=item.get("description"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _collect_gnews_news(query: str, limit: int) -> List[NewsArticle]:
    credential = get_external_provider_credential("gnews")
    if credential is None:
        raise MissingNewsCredentialError
    encoded_query = urllib.parse.urlencode(
        {
            "q": query,
            "lang": "en",
            "max": str(limit),
            "apikey": credential.api_key,
        }
    )
    payload = _fetch_json(f"https://gnews.io/api/v4/search?{encoded_query}")
    articles: List[NewsArticle] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("articles", []))[:limit]):
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        source_name = source.get("name") if isinstance(source, dict) else source
        article = _article(
            provider="gnews_news",
            query=query,
            rank=index,
            title=item.get("title"),
            url=item.get("url"),
            source=source_name,
            published_at=item.get("publishedAt"),
            snippet=item.get("description") or item.get("content"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _serpapi_source_name(item: Dict[str, Any]) -> Optional[str]:
    source = item.get("source")
    if isinstance(source, dict):
        return _clean_text(source.get("name")) or None
    return _clean_text(source) or None


def _serpapi_news_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_results = payload.get("news_results")
    if not isinstance(raw_results, list):
        return []
    rows: List[Dict[str, Any]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        stories = item.get("stories")
        if isinstance(stories, list):
            rows.extend(
                cast(
                    List[Dict[str, Any]],
                    [story for story in stories if isinstance(story, dict)],
                )
            )
            continue
        rows.append(item)
    return rows


def _collect_serpapi_google_news(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    credential = get_external_provider_credential("serpapi")
    if credential is None:
        raise MissingNewsCredentialError
    encoded_query = urllib.parse.urlencode(
        {
            "engine": "google_news",
            "q": query,
            "gl": "kr" if quote.market == "KR" else "us",
            "hl": "ko" if quote.market == "KR" else "en",
            "api_key": credential.api_key,
        }
    )
    payload = _fetch_json(f"{SERPAPI_SEARCH_URL}?{encoded_query}")
    articles: List[NewsArticle] = []
    for index, item in enumerate(_serpapi_news_rows(payload)[:limit]):
        article = _article(
            provider="serpapi_google_news",
            query=query,
            rank=index,
            title=item.get("title") or item.get("snippet"),
            url=item.get("link") or item.get("url"),
            source=_serpapi_source_name(item),
            published_at=item.get("date") or item.get("published_at"),
            snippet=item.get("snippet") or item.get("summary"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _collect_serpapi_google_web(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    credential = get_external_provider_credential("serpapi")
    if credential is None:
        raise MissingNewsCredentialError
    encoded_query = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "location": "South Korea" if quote.market == "KR" else "United States",
            "google_domain": "google.com",
            "hl": "ko" if quote.market == "KR" else "en",
            "gl": "kr" if quote.market == "KR" else "us",
            "api_key": credential.api_key,
        }
    )
    payload = _fetch_json(f"{SERPAPI_SEARCH_URL}?{encoded_query}")
    articles: List[NewsArticle] = []
    for index, item in enumerate(
        cast(List[Dict[str, Any]], payload.get("organic_results", []))[:limit]
    ):
        if not isinstance(item, dict):
            continue
        article = _article(
            provider="serpapi_google_web",
            query=query,
            rank=index,
            title=item.get("title"),
            url=item.get("link"),
            source=item.get("source"),
            published_at=item.get("date"),
            snippet=item.get("snippet"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _collect_serpapi_social_web(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    articles = _collect_serpapi_google_web(query, limit, quote)
    return [
        article.model_copy(update={"provider": "serpapi_social_web"})
        for article in articles
        if article.source_domain in {"x.com", "twitter.com", "facebook.com"}
    ]


def _collect_provider(
    provider: NewsProvider,
    query: str,
    limit: int,
    quote: MarketQuote,
) -> List[NewsArticle]:
    if provider == "tavily_news":
        return _collect_tavily_news(query, limit)
    if provider == "naver_news":
        return _collect_naver_news(query, limit)
    if provider == "gnews_news":
        return _collect_gnews_news(query, limit)
    if provider == "serpapi_google_news":
        return _collect_serpapi_google_news(query, limit, quote)
    if provider == "serpapi_social_web":
        return _collect_serpapi_social_web(query, limit, quote)
    return _collect_serpapi_google_web(query, limit, quote)


def _provider_cache_components(
    provider: NewsProvider,
    query: str,
    limit: int,
    quote: MarketQuote,
) -> Dict[str, Any]:
    return {
        "provider": provider,
        "query": query,
        "limit": limit,
        "market": quote.market,
        "symbol": quote.symbol,
        "provider_version": "phase_093_news_provider_v1",
    }


def _collect_provider_with_cache(
    provider: NewsProvider,
    query: str,
    limit: int,
    quote: MarketQuote,
    store: Optional[LocalStateStore],
    cache_ttl_seconds: int,
) -> Tuple[List[NewsArticle], bool]:
    components = _provider_cache_components(provider, query, limit, quote)
    if store is not None:
        cached_payload = get_cached_json(store, "news_provider_result", components)
        if cached_payload is not None:
            cached_articles = cached_payload.get("articles")
            if isinstance(cached_articles, list):
                return (
                    [
                        NewsArticle(**article)
                        for article in cached_articles
                        if isinstance(article, dict)
                    ],
                    True,
                )

    articles = _collect_provider(provider, query, limit, quote)
    if store is not None:
        set_cached_json(
            store,
            "news_provider_result",
            components,
            {"articles": [_model_dump(article) for article in articles]},
            ttl_seconds=cache_ttl_seconds,
        )
    return articles, False


def _dedupe_key(article: NewsArticle) -> str:
    if article.url:
        return f"url:{article.url}"
    normalized_title = re.sub(r"[^a-z0-9가-힣]+", " ", article.title.lower()).strip()
    return f"title:{normalized_title}"


def _parse_sort_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _sort_timestamp(value: Optional[str]) -> float:
    parsed = _parse_sort_datetime(value)
    return parsed.timestamp() if parsed is not None else 0.0


def _rank_articles(articles: Iterable[NewsArticle]) -> List[NewsArticle]:
    deduped: Dict[str, NewsArticle] = {}
    for article in articles:
        key = _dedupe_key(article)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = article
            continue
        existing_datetime = _parse_sort_datetime(existing.published_at)
        article_datetime = _parse_sort_datetime(article.published_at)
        if article_datetime is not None and (
            existing_datetime is None or article_datetime > existing_datetime
        ):
            deduped[key] = article

    return sorted(
        deduped.values(),
        key=lambda article: (
            -article.importance_score,
            -_sort_timestamp(article.published_at),
            PROVIDER_PRIORITY[article.provider],
            article.rank,
            article.title,
        ),
    )


def _select_diverse_articles(
    ranked_articles: Iterable[NewsArticle],
    limit: int,
) -> List[NewsArticle]:
    if limit <= 0:
        return []

    ranked = list(ranked_articles)
    selected: List[NewsArticle] = []
    selected_ids: set[str] = set()
    category_counts: Dict[NewsCategory, int] = {}
    domain_counts: Dict[str, int] = {}

    def select(article: NewsArticle) -> None:
        selected.append(article)
        selected_ids.add(article.id)
        category_counts[article.category] = category_counts.get(article.category, 0) + 1
        if article.source_domain:
            domain_counts[article.source_domain] = domain_counts.get(article.source_domain, 0) + 1

    def can_select(
        article: NewsArticle,
        *,
        max_category_count: int,
        max_domain_count: int,
        include_quote_pages: bool,
    ) -> bool:
        if article.id in selected_ids:
            return False
        if len(selected) >= limit:
            return False
        if not include_quote_pages and article.category == "quote_page":
            return False
        if category_counts.get(article.category, 0) >= max_category_count:
            return False
        if article.source_domain and domain_counts.get(article.source_domain, 0) >= max_domain_count:
            return False
        return True

    for max_category_count, max_domain_count, include_quote_pages in (
        (2, 2, False),
        (3, 3, False),
        (10_000, 10_000, True),
    ):
        for article in ranked:
            if can_select(
                article,
                max_category_count=max_category_count,
                max_domain_count=max_domain_count,
                include_quote_pages=include_quote_pages,
            ):
                select(article)
        if len(selected) >= limit:
            break

    return selected


def _fallback_summary(
    *,
    quote: MarketQuote,
    article_count: int,
    important_count: int,
    language: str,
) -> str:
    if language == "ko":
        return (
            f"{quote.name} ({quote.symbol}) 관련 최신 뉴스 {article_count}건을 확인했고, "
            f"중요도가 높은 {important_count}건을 먼저 정리했습니다."
        )
    return (
        f"I found {article_count} recent news item(s) for {quote.name} "
        f"({quote.symbol}) and highlighted the top {important_count}."
    )


def _key_points(articles: List[NewsArticle], language: str) -> List[str]:
    points: List[str] = []
    for article in articles:
        source = f" - {article.source}" if article.source else ""
        if language == "ko":
            points.append(f"{article.title}{source}")
        else:
            points.append(f"{article.title}{source}")
    return points


def create_news_digest(
    quote: MarketQuote,
    *,
    requested_query: str,
    language: str,
    providers: Tuple[NewsProvider, ...] = DEFAULT_NEWS_PROVIDERS,
    provider_limit: int = 10,
    important_limit: int = 5,
    additional_limit: int = 10,
    store: Optional[LocalStateStore] = None,
    cache_ttl_seconds: int = NEWS_PROVIDER_CACHE_TTL_SECONDS,
) -> NewsDigest:
    queries = _build_news_queries(quote, requested_query)
    query = queries[0]
    active_providers = _expand_default_providers(providers, requested_query)
    articles: List[NewsArticle] = []
    provider_runs: List[NewsSearchRun] = []
    warnings: List[str] = []
    cache_hits = 0
    cache_misses = 0

    for provider in active_providers:
        for provider_query in _provider_queries(
            provider,
            queries,
            quote=quote,
            requested_query=requested_query,
        ):
            try:
                provider_articles, cache_hit = _collect_provider_with_cache(
                    provider,
                    provider_query,
                    provider_limit,
                    quote,
                    store,
                    cache_ttl_seconds,
                )
                if cache_hit:
                    cache_hits += 1
                else:
                    cache_misses += 1
                run_status: NewsProviderRunStatus = "completed"
                warning = None
            except MissingNewsCredentialError:
                provider_articles = []
                run_status = "missing_credential"
                warning = record_provider_warning(warnings, run_status, provider)
            except NewsProviderError:
                provider_articles = []
                run_status = "provider_error"
                warning = record_provider_warning(warnings, run_status, provider)
            articles.extend(provider_articles)
            provider_runs.append(
                NewsSearchRun(
                    provider=provider,
                    query=provider_query,
                    result_count=len(provider_articles),
                    status=run_status,
                    warning=warning,
                )
            )

    ranked_articles = _rank_articles(articles)
    important_articles = _select_diverse_articles(ranked_articles, important_limit)
    important_article_ids = {article.id for article in important_articles}
    additional_articles = [
        article for article in ranked_articles if article.id not in important_article_ids
    ][:additional_limit]
    if ranked_articles:
        status: NewsSearchStatus = "completed" if not warnings else "partial"
    else:
        status = "empty"

    summary = _fallback_summary(
        quote=quote,
        article_count=len(ranked_articles),
        important_count=len(important_articles),
        language=language,
    )
    digest = NewsDigest(
        digest_id=f"digest_{uuid4().hex}",
        status=status,
        market=quote.market,
        symbol=quote.symbol,
        stock_name=quote.name,
        query=query,
        generated_at=_now(),
        summary=summary,
        key_points=_key_points(important_articles, language),
        important_articles=important_articles,
        additional_articles=additional_articles,
        provider_runs=provider_runs,
        warnings=warnings,
    )
    if store is not None:
        record_news_processing_run(
            store,
            digest_payload=_model_dump(digest),
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            query_templates=queries,
        )
    return digest
