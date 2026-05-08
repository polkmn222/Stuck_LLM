import html
import json
import re
import socket
from ipaddress import ip_address
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, cast
from uuid import uuid4

from app.features.credentials.external_providers import (
    get_external_provider_credential,
    get_naver_search_credential,
)
from app.features.credentials.schemas import ExternalCredentialProvider
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
from app.shared.datetime_utils import parse_optional_aware_datetime
from app.shared.pydantic_compat import model_dump as _model_dump
from app.shared.state_store import LocalStateStore

HTML_TAG_RE = re.compile(r"<[^>]+>")
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
FREE_RSS_NEWS_PROVIDERS: Tuple[NewsProvider, ...] = (
    "seekingalpha_rss",
    "yahoo_finance_rss",
    "google_news_rss",
    "bing_news_rss",
)
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
REDDIT_PUBLIC_SEARCH_SUBREDDITS: Tuple[str, ...] = (
    "stocks",
    "investing",
    "SecurityAnalysis",
    "ValueInvesting",
)
PROVIDER_PRIORITY: Dict[NewsProvider, int] = {
    "seekingalpha_rss": 0,
    "yahoo_finance_rss": 1,
    "google_news_rss": 2,
    "bing_news_rss": 3,
    "eventregistry_news": 4,
    "tavily_news": 5,
    "naver_news": 6,
    "gnews_news": 7,
    "serpapi_google_news": 8,
    "serpapi_google_web": 9,
    "serpapi_social_web": 10,
    "reddit_public_search": 11,
    "web_crawl": 12,
    "reddit_crawl": 13,
}
NEWS_QUERY_SUFFIX = "latest company news earnings official business controversy"
SOCIAL_QUERY_SUFFIX = (
    "(site:x.com OR site:twitter.com OR site:facebook.com) public posts CEO leadership policy investor reaction"
)
NEWS_PROVIDER_CACHE_TTL_SECONDS = 15 * 60
SNIPPET_MAX_LENGTH = 260
CRAWL_MAX_BYTES = 200_000
URL_RE = re.compile(r"https?://[^\s<>'\")\]]+")
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


ExternalCredentialMap = Mapping[ExternalCredentialProvider, str]


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


def _is_official_domain(domain: str) -> bool:
    return any(
        domain == official or domain.endswith(f".{official}")
        for official in OFFICIAL_DOMAINS
    )


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
    if _is_official_domain(domain):
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
    if _is_official_domain(domain):
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
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise NewsProviderError("News provider request failed:429") from None
        raise NewsProviderError("News provider request failed.") from None
    except (TimeoutError, urllib.error.URLError, OSError, ValueError):
        raise NewsProviderError("News provider request failed.") from None
    if not isinstance(data, dict):
        raise NewsProviderError("News provider response was malformed.")
    return cast(Dict[str, Any], data)


def _external_api_key(
    provider: ExternalCredentialProvider,
    external_credentials: Optional[ExternalCredentialMap],
) -> str:
    if external_credentials is not None:
        api_key = external_credentials.get(provider)
        if api_key:
            return api_key
        raise MissingNewsCredentialError
    credential = get_external_provider_credential(cast(Any, provider))
    if credential is None:
        raise MissingNewsCredentialError
    return credential.api_key


def _fetch_text(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 10,
) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.5",
            "User-Agent": "Stuck_LLM/0.1 news rss collector",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read(CRAWL_MAX_BYTES).decode(charset, errors="replace")
    except (TimeoutError, urllib.error.HTTPError, urllib.error.URLError, OSError):
        raise NewsProviderError("RSS provider request failed.") from None


def _literal_ip(hostname: str) -> Optional[str]:
    try:
        return str(ip_address(hostname))
    except ValueError:
        return None


def _unsafe_crawl_ip(value: str) -> bool:
    try:
        address = ip_address(value)
    except ValueError:
        return False
    return (
        str(address) == "169.254.169.254"
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _unsafe_crawl_host(hostname: str) -> bool:
    normalized = hostname.lower().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain"}:
        return True
    if normalized.endswith((".localhost", ".local", ".internal")):
        return True
    literal_ip = _literal_ip(normalized)
    return literal_ip is not None and _unsafe_crawl_ip(literal_ip)


def _crawl_host_resolves_unsafely(hostname: str, port: Optional[int]) -> bool:
    try:
        normalized = hostname.rstrip(".").encode("idna").decode("ascii")
        rows = socket.getaddrinfo(
            normalized,
            port or 443,
            type=socket.SOCK_STREAM,
        )
    except (OSError, UnicodeError):
        return True

    addresses: List[str] = []
    for row in rows:
        sockaddr = row[4]
        if isinstance(sockaddr, tuple) and sockaddr:
            addresses.append(str(sockaddr[0]))
    return not addresses or any(_unsafe_crawl_ip(address) for address in addresses)


def _safe_crawl_url(value: str, *, resolve_host: bool = True) -> Optional[str]:
    raw_url = value.strip().rstrip(".,;")
    try:
        parsed = urllib.parse.urlsplit(raw_url)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc or parsed.hostname is None:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if _unsafe_crawl_host(parsed.hostname):
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if resolve_host and _crawl_host_resolves_unsafely(parsed.hostname, port):
        return None
    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def _extract_user_urls(text: str) -> Tuple[str, ...]:
    urls: List[str] = []
    seen: set[str] = set()
    for match in URL_RE.finditer(text):
        safe_url = _safe_crawl_url(match.group(0), resolve_host=False)
        if safe_url is None or safe_url in seen:
            continue
        seen.add(safe_url)
        urls.append(safe_url)
    return tuple(urls)


def _fetch_url_text(url: str, timeout_seconds: int = 10) -> str:
    safe_url = _safe_crawl_url(url)
    if safe_url is None:
        raise NewsProviderError("URL is not allowed for crawling.")
    request = urllib.request.Request(
        safe_url,
        headers={
            "Accept": "text/html,application/xhtml+xml,text/plain,application/json;q=0.8,*/*;q=0.5",
            "User-Agent": "Stuck_LLM/0.1 research crawler",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            if final_url and _safe_crawl_url(final_url) is None:
                raise NewsProviderError("Crawl redirect target is not allowed.")
            content_type = response.headers.get("content-type", "")
            content_type_lower = content_type.lower()
            if content_type and not any(
                kind in content_type_lower for kind in ("html", "text", "json")
            ):
                raise NewsProviderError("Crawl response type is not supported.")
            data = response.read(CRAWL_MAX_BYTES + 1)
    except (TimeoutError, urllib.error.HTTPError, urllib.error.URLError, OSError):
        raise NewsProviderError("URL crawl failed.") from None
    if len(data) > CRAWL_MAX_BYTES:
        data = data[:CRAWL_MAX_BYTES]
    return data.decode("utf-8", errors="replace")


def _html_title(markup: str, fallback_url: str) -> str:
    for pattern in (
        r"<meta\s+property=[\"']og:title[\"']\s+content=[\"']([^\"']+)[\"']",
        r"<meta\s+name=[\"']twitter:title[\"']\s+content=[\"']([^\"']+)[\"']",
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
    ):
        match = re.search(pattern, markup, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title = _clean_text(match.group(1))
            if title:
                return title
    return fallback_url


def _html_published_at(markup: str) -> Optional[str]:
    for pattern in (
        r"<meta\s+property=[\"']article:published_time[\"']\s+content=[\"']([^\"']+)[\"']",
        r"<meta\s+name=[\"']date[\"']\s+content=[\"']([^\"']+)[\"']",
        r"<time[^>]+datetime=[\"']([^\"']+)[\"']",
    ):
        match = re.search(pattern, markup, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _normalize_published_at(match.group(1))
    return None


def _html_snippet(markup: str) -> Optional[str]:
    article_match = re.search(
        r"<article[^>]*>(.*?)</article>",
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    )
    selected = article_match.group(1) if article_match else markup
    selected = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", selected, flags=re.IGNORECASE | re.DOTALL)
    return _truncate_text(selected, max_length=500)


def _crawl_web_article(url: str, query: str) -> Optional[NewsArticle]:
    safe_url = _safe_crawl_url(url, resolve_host=False)
    if safe_url is None:
        raise NewsProviderError("URL is not allowed for crawling.")
    markup = _fetch_url_text(safe_url)
    title = _html_title(markup, safe_url)
    return _article(
        provider="web_crawl",
        query=query,
        rank=0,
        title=title,
        url=safe_url,
        source=_source_from_url(safe_url),
        published_at=_html_published_at(markup),
        snippet=_html_snippet(markup),
    )


def _reddit_search_api_url(url: str) -> Optional[str]:
    parsed = urllib.parse.urlsplit(url)
    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    if hostname != "reddit.com" or not parsed.path.startswith("/search"):
        return None
    query = urllib.parse.parse_qs(parsed.query).get("q", [""])[0].strip()
    if not query:
        return None
    encoded = urllib.parse.urlencode(
        {
            "q": query,
            "sort": "relevance",
            "t": "month",
            "limit": "10",
        }
    )
    return f"https://www.reddit.com/search.json?{encoded}"


def _collect_reddit_search_url(url: str, limit: int) -> List[NewsArticle]:
    api_url = _reddit_search_api_url(url)
    if api_url is None:
        raise NewsProviderError("Reddit search URL is not supported.")
    payload = _fetch_json(
        api_url,
        headers={"User-Agent": "Stuck_LLM/0.1 research crawler"},
    )
    raw_children = payload.get("data")
    children = raw_children.get("children", []) if isinstance(raw_children, dict) else []
    articles: List[NewsArticle] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], children)[:limit]):
        if not isinstance(item, dict) or not isinstance(item.get("data"), dict):
            continue
        data = cast(Dict[str, Any], item["data"])
        permalink = _clean_text(data.get("permalink"))
        article_url = (
            f"https://www.reddit.com{permalink}"
            if permalink.startswith("/")
            else permalink or url
        )
        created_utc = data.get("created_utc")
        published_at = None
        if isinstance(created_utc, (int, float)):
            published_at = datetime.fromtimestamp(created_utc, timezone.utc).isoformat()
        article = _article(
            provider="reddit_crawl",
            query=url,
            rank=index,
            title=data.get("title"),
            url=article_url,
            source=data.get("subreddit_name_prefixed") or "Reddit",
            published_at=published_at,
            snippet=data.get("selftext") or data.get("title"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _reddit_article_from_post(
    *,
    provider: NewsProvider,
    query: str,
    rank: int,
    data: Dict[str, Any],
) -> Optional[NewsArticle]:
    permalink = _clean_text(data.get("permalink"))
    article_url = (
        f"https://www.reddit.com{permalink}"
        if permalink.startswith("/")
        else permalink or _clean_text(data.get("url"))
    )
    created_utc = data.get("created_utc")
    published_at = None
    if isinstance(created_utc, (int, float)):
        published_at = datetime.fromtimestamp(created_utc, timezone.utc).isoformat()
    return _article(
        provider=provider,
        query=query,
        rank=rank,
        title=data.get("title"),
        url=article_url,
        source=data.get("subreddit_name_prefixed") or "Reddit",
        published_at=published_at,
        snippet=data.get("selftext") or data.get("title"),
    )


def _collect_reddit_public_search(query: str, limit: int) -> Tuple[List[NewsArticle], int]:
    articles: List[NewsArticle] = []
    seen: set[str] = set()
    failed_requests = 0
    per_subreddit_limit = max(1, min(limit, 10))
    for subreddit in REDDIT_PUBLIC_SEARCH_SUBREDDITS:
        encoded = urllib.parse.urlencode(
            {
                "q": query,
                "restrict_sr": "1",
                "sort": "relevance",
                "t": "month",
                "limit": str(per_subreddit_limit),
            }
        )
        url = f"https://old.reddit.com/r/{subreddit}/search.json?{encoded}"
        try:
            payload = _fetch_json(
                url,
                headers={"User-Agent": "Stuck_LLM/0.1 reddit public search"},
            )
        except NewsProviderError as error:
            failed_requests += 1
            if _is_rate_limit_error(error):
                break
            continue
        raw_children = payload.get("data")
        children = raw_children.get("children", []) if isinstance(raw_children, dict) else []
        for item in cast(List[Dict[str, Any]], children):
            if not isinstance(item, dict) or not isinstance(item.get("data"), dict):
                continue
            article = _reddit_article_from_post(
                provider="reddit_public_search",
                query=query,
                rank=len(articles),
                data=cast(Dict[str, Any], item["data"]),
            )
            if article is None:
                continue
            key = _dedupe_key(article)
            title_key = f"title:{re.sub(r'[^a-z0-9가-힣]+', ' ', article.title.lower()).strip()}"
            if key in seen or title_key in seen:
                continue
            seen.add(key)
            seen.add(title_key)
            articles.append(article)
            if len(articles) >= limit:
                return articles, failed_requests
    if not articles and failed_requests:
        raise NewsProviderError("Reddit public search failed.")
    return articles, failed_requests


def _is_rate_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    return "429" in message or "rate limit" in message or "rate-limited" in message


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _xml_child_text(element: ET.Element, *names: str) -> Optional[str]:
    expected = {name.lower() for name in names}
    for child in list(element):
        if _xml_local_name(child.tag) in expected:
            return child.text
    return None


def _rss_items(xml: str) -> List[ET.Element]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        raise NewsProviderError("RSS provider response was malformed.") from None
    return [
        element
        for element in root.iter()
        if _xml_local_name(element.tag) == "item"
    ]


def _rss_articles(
    *,
    provider: NewsProvider,
    query: str,
    xml: str,
    source_fallback: str,
    limit: int,
) -> List[NewsArticle]:
    articles: List[NewsArticle] = []
    for index, item in enumerate(_rss_items(xml)[:limit]):
        source = _xml_child_text(item, "source") or source_fallback
        article = _article(
            provider=provider,
            query=query,
            rank=index,
            title=_xml_child_text(item, "title"),
            url=_xml_child_text(item, "link", "guid"),
            source=source,
            published_at=_xml_child_text(item, "pubDate", "published", "updated"),
            snippet=_xml_child_text(item, "description", "summary"),
        )
        if article is not None:
            articles.append(article)
    return articles


def _rss_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        )
    }


def _collect_seekingalpha_rss(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    if quote.market != "US":
        return []
    ticker = urllib.parse.quote(quote.symbol.upper())
    url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
    return _rss_articles(
        provider="seekingalpha_rss",
        query=query,
        xml=_fetch_text(url, headers=_rss_headers()),
        source_fallback="Seeking Alpha",
        limit=limit,
    )


def _yahoo_finance_rss_symbol(quote: MarketQuote) -> str:
    if quote.market == "KR" and not quote.symbol.endswith((".KS", ".KQ")):
        return f"{quote.symbol}.KS"
    return quote.symbol


def _collect_yahoo_finance_rss(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    region = "KR" if quote.market == "KR" else "US"
    locale = "ko-KR" if quote.market == "KR" else "en-US"
    encoded = urllib.parse.urlencode(
        {
            "s": _yahoo_finance_rss_symbol(quote),
            "region": region,
            "lang": locale,
        }
    )
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?{encoded}"
    return _rss_articles(
        provider="yahoo_finance_rss",
        query=query,
        xml=_fetch_text(url, headers=_rss_headers()),
        source_fallback="Yahoo Finance",
        limit=limit,
    )


def _collect_google_news_rss(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    params = {
        "q": f"{query} stock",
        "hl": "ko" if quote.market == "KR" else "en-US",
        "gl": "KR" if quote.market == "KR" else "US",
        "ceid": "KR:ko" if quote.market == "KR" else "US:en",
    }
    url = f"https://news.google.com/rss/search?{urllib.parse.urlencode(params)}"
    return _rss_articles(
        provider="google_news_rss",
        query=query,
        xml=_fetch_text(url, headers=_rss_headers()),
        source_fallback="Google News",
        limit=limit,
    )


def _collect_bing_news_rss(query: str, limit: int, quote: MarketQuote) -> List[NewsArticle]:
    encoded = urllib.parse.urlencode(
        {
            "q": f"{query} stock",
            "format": "rss",
            "mkt": "ko-KR" if quote.market == "KR" else "en-US",
        }
    )
    url = f"https://www.bing.com/news/search?{encoded}"
    return _rss_articles(
        provider="bing_news_rss",
        query=query,
        xml=_fetch_text(url, headers=_rss_headers()),
        source_fallback="Bing News",
        limit=limit,
    )


def _eventregistry_source_name(item: Dict[str, Any]) -> Optional[str]:
    source = item.get("source")
    if isinstance(source, dict):
        return _clean_text(source.get("title") or source.get("name") or source.get("uri")) or None
    return _clean_text(source) or None


def _eventregistry_date_window(quote: MarketQuote) -> Tuple[str, str]:
    parsed = parse_optional_aware_datetime(quote.as_of_at)
    end_date = (parsed or datetime.now(timezone.utc)).date()
    start_date = end_date - timedelta(days=30)
    return start_date.isoformat(), end_date.isoformat()


def _collect_eventregistry_news(
    query: str,
    limit: int,
    quote: MarketQuote,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    api_key = _external_api_key("eventregistry", external_credentials)
    date_start, date_end = _eventregistry_date_window(quote)
    payload: Dict[str, Any] = {
        "apiKey": api_key,
        "action": "getArticles",
        "keyword": query,
        "keywordLoc": "body,title",
        "keywordSearchMode": "phrase",
        "dateStart": date_start,
        "dateEnd": date_end,
        "isDuplicateFilter": "skipDuplicates",
        "dataType": "news",
        "forceMaxDataTimeWindow": 31,
        "articlesPage": 1,
        "articlesCount": min(max(limit, 1), 100),
        "articlesSortBy": "date",
        "articlesSortByAsc": False,
        "includeArticleBasicInfo": True,
        "includeArticleTitle": True,
        "includeArticleBody": True,
        "includeArticleUrl": True,
        "includeArticleAuthors": False,
        "includeArticleSentiment": True,
        "articleBodyLen": 800,
        "resultType": "articles",
    }
    if quote.market == "US":
        payload["lang"] = "eng"
    response = _fetch_json(
        "https://www.eventregistry.org/api/v1/article",
        headers={"Accept": "application/json"},
        payload=payload,
        timeout_seconds=15,
    )
    raw_articles = response.get("articles")
    if not isinstance(raw_articles, dict):
        raise NewsProviderError("EventRegistry response was malformed.")
    raw_results = raw_articles.get("results", [])
    if not isinstance(raw_results, list):
        raise NewsProviderError("EventRegistry response was malformed.")
    articles: List[NewsArticle] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], raw_results)[:limit]):
        if not isinstance(item, dict):
            continue
        article = _article(
            provider="eventregistry_news",
            query=query,
            rank=index,
            title=item.get("title"),
            url=item.get("url"),
            source=_eventregistry_source_name(item),
            published_at=item.get("dateTimePub") or item.get("date") or item.get("publishedAt"),
            snippet=item.get("body") or item.get("summary"),
        )
        if article is not None:
            articles.append(article)
    return articles


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
        summary_ko=None,
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


def _reddit_public_search_requested(requested_query: str) -> bool:
    text = _combined_text(requested_query)
    return _contains_any_keyword(
        text,
        (
            "reddit",
            "레딧",
            "community",
            "communities",
            "forum",
            "forums",
            "커뮤니티",
            "게시판",
            "investor sentiment",
            "retail sentiment",
            "sentiment",
            "social reaction",
            "market reaction",
            "investor reaction",
            "retail reaction",
            "투자자 심리",
            "투자 심리",
            "투자심리",
            "시장 반응",
            "투자자 반응",
            "여론",
        ),
    )


def _has_external_api_key(
    provider: ExternalCredentialProvider,
    external_credentials: Optional[ExternalCredentialMap],
) -> bool:
    if external_credentials is not None:
        return bool(external_credentials.get(provider))
    return get_external_provider_credential(cast(Any, provider)) is not None


def _expand_default_providers(
    providers: Tuple[NewsProvider, ...],
    requested_query: str,
    external_credentials: Optional[ExternalCredentialMap],
) -> Tuple[NewsProvider, ...]:
    if providers != DEFAULT_NEWS_PROVIDERS:
        return providers
    expanded: List[NewsProvider] = []
    if _has_external_api_key("tavily", external_credentials):
        expanded.append("tavily_news")
    if _has_external_api_key("gnews", external_credentials):
        expanded.append("gnews_news")
    if _has_external_api_key("serpapi", external_credentials):
        expanded.extend(("serpapi_google_news", "serpapi_google_web"))
    if _has_external_api_key("eventregistry", external_credentials):
        expanded.append("eventregistry_news")
    if not expanded and get_naver_search_credential() is None:
        expanded.extend(FREE_RSS_NEWS_PROVIDERS)
    if get_naver_search_credential() is not None:
        expanded.append("naver_news")
    if (
        _has_external_api_key("serpapi", external_credentials)
        and _social_source_requested(requested_query)
    ):
        expanded.append("serpapi_social_web")
    if _reddit_public_search_requested(requested_query):
        expanded.append("reddit_public_search")
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
    if provider == "reddit_public_search":
        requested = _clean_text(requested_query)
        company = f"{quote.name} {quote.symbol}"
        return _dedupe_queries((f"{company} {requested}" if requested else queries[0],))
    if (
        provider in FREE_RSS_NEWS_PROVIDERS
        or provider == "eventregistry_news"
    ):
        return (queries[0],)
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


def _collect_tavily_news(
    query: str,
    limit: int,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    api_key = _external_api_key("tavily", external_credentials)
    payload = _fetch_json(
        "https://api.tavily.com/search",
        payload={
            "api_key": api_key,
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


def _collect_gnews_news(
    query: str,
    limit: int,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    api_key = _external_api_key("gnews", external_credentials)
    encoded_query = urllib.parse.urlencode(
        {
            "q": query,
            "lang": "en",
            "max": str(limit),
            "apikey": api_key,
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


def _collect_serpapi_google_news(
    query: str,
    limit: int,
    quote: MarketQuote,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    api_key = _external_api_key("serpapi", external_credentials)
    encoded_query = urllib.parse.urlencode(
        {
            "engine": "google_news",
            "q": query,
            "gl": "kr" if quote.market == "KR" else "us",
            "hl": "ko" if quote.market == "KR" else "en",
            "api_key": api_key,
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


def _collect_serpapi_google_web(
    query: str,
    limit: int,
    quote: MarketQuote,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    api_key = _external_api_key("serpapi", external_credentials)
    encoded_query = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "location": "South Korea" if quote.market == "KR" else "United States",
            "google_domain": "google.com",
            "hl": "ko" if quote.market == "KR" else "en",
            "gl": "kr" if quote.market == "KR" else "us",
            "api_key": api_key,
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


def _collect_serpapi_social_web(
    query: str,
    limit: int,
    quote: MarketQuote,
    external_credentials: Optional[ExternalCredentialMap],
) -> List[NewsArticle]:
    articles = _collect_serpapi_google_web(query, limit, quote, external_credentials)
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
    external_credentials: Optional[ExternalCredentialMap],
) -> Tuple[List[NewsArticle], Optional[NewsProviderRunStatus]]:
    if provider == "eventregistry_news":
        return _collect_eventregistry_news(query, limit, quote, external_credentials), None
    if provider == "reddit_public_search":
        articles, failed_requests = _collect_reddit_public_search(query, limit)
        warning_status: Optional[NewsProviderRunStatus] = (
            "partial_provider_error" if failed_requests else None
        )
        return articles, warning_status
    if provider == "seekingalpha_rss":
        return _collect_seekingalpha_rss(query, limit, quote), None
    if provider == "yahoo_finance_rss":
        return _collect_yahoo_finance_rss(query, limit, quote), None
    if provider == "google_news_rss":
        return _collect_google_news_rss(query, limit, quote), None
    if provider == "bing_news_rss":
        return _collect_bing_news_rss(query, limit, quote), None
    if provider == "tavily_news":
        return _collect_tavily_news(query, limit, external_credentials), None
    if provider == "naver_news":
        return _collect_naver_news(query, limit), None
    if provider == "gnews_news":
        return _collect_gnews_news(query, limit, external_credentials), None
    if provider == "serpapi_google_news":
        return _collect_serpapi_google_news(query, limit, quote, external_credentials), None
    if provider == "serpapi_social_web":
        return _collect_serpapi_social_web(query, limit, quote, external_credentials), None
    return _collect_serpapi_google_web(query, limit, quote, external_credentials), None


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
        "provider_version": "phase_143_news_provider_v2",
    }


def _collect_provider_with_cache(
    provider: NewsProvider,
    query: str,
    limit: int,
    quote: MarketQuote,
    store: Optional[LocalStateStore],
    cache_ttl_seconds: int,
    external_credentials: Optional[ExternalCredentialMap],
) -> Tuple[List[NewsArticle], bool, Optional[NewsProviderRunStatus]]:
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
                    None,
                )

    articles, warning_status = _collect_provider(
        provider,
        query,
        limit,
        quote,
        external_credentials,
    )
    if store is not None:
        set_cached_json(
            store,
            "news_provider_result",
            components,
            {"articles": [_model_dump(article) for article in articles]},
            ttl_seconds=cache_ttl_seconds,
        )
    return articles, False, warning_status


def _dedupe_key(article: NewsArticle) -> str:
    if article.url:
        return f"url:{article.url}"
    normalized_title = re.sub(r"[^a-z0-9가-힣]+", " ", article.title.lower()).strip()
    return f"title:{normalized_title}"


def _parse_sort_datetime(value: Optional[str]) -> Optional[datetime]:
    return parse_optional_aware_datetime(value)


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


def _collect_user_url_articles(
    requested_query: str,
    *,
    provider_limit: int,
) -> Tuple[List[NewsArticle], List[NewsSearchRun], List[str]]:
    articles: List[NewsArticle] = []
    runs: List[NewsSearchRun] = []
    warnings: List[str] = []

    for url in _extract_user_urls(requested_query):
        reddit_api_url = _reddit_search_api_url(url)
        provider: NewsProvider = "reddit_crawl" if reddit_api_url is not None else "web_crawl"
        try:
            provider_articles = (
                _collect_reddit_search_url(url, provider_limit)
                if provider == "reddit_crawl"
                else [article for article in [_crawl_web_article(url, url)] if article is not None]
            )
            run_status: NewsProviderRunStatus = "completed"
            warning = None
        except NewsProviderError:
            provider_articles = []
            run_status = "provider_error"
            warning = record_provider_warning(warnings, run_status, provider)
        articles.extend(provider_articles)
        runs.append(
            NewsSearchRun(
                provider=provider,
                query=url,
                result_count=len(provider_articles),
                status=run_status,
                warning=warning,
            )
        )

    return articles, runs, warnings


def create_news_digest(
    quote: MarketQuote,
    *,
    requested_query: str,
    language: str,
    providers: Tuple[NewsProvider, ...] = DEFAULT_NEWS_PROVIDERS,
    provider_limit: int = 10,
    important_limit: int = 5,
    additional_limit: int = 10,
    query_limit: Optional[int] = None,
    store: Optional[LocalStateStore] = None,
    cache_ttl_seconds: int = NEWS_PROVIDER_CACHE_TTL_SECONDS,
    external_credentials: Optional[ExternalCredentialMap] = None,
) -> NewsDigest:
    queries = _build_news_queries(quote, requested_query)
    if query_limit is not None and query_limit > 0:
        queries = queries[:query_limit]
    query = queries[0]
    active_providers = _expand_default_providers(
        providers,
        requested_query,
        external_credentials,
    )
    articles: List[NewsArticle] = []
    provider_runs: List[NewsSearchRun] = []
    warnings: List[str] = []
    cache_hits = 0
    cache_misses = 0
    url_articles, url_runs, url_warnings = _collect_user_url_articles(
        requested_query,
        provider_limit=provider_limit,
    )
    articles.extend(url_articles)
    provider_runs.extend(url_runs)
    warnings.extend(url_warnings)

    for provider in active_providers:
        for provider_query in _provider_queries(
            provider,
            queries,
            quote=quote,
            requested_query=requested_query,
        ):
            try:
                provider_articles, cache_hit, warning_status = _collect_provider_with_cache(
                    provider,
                    provider_query,
                    provider_limit,
                    quote,
                    store,
                    cache_ttl_seconds,
                    external_credentials,
                )
                if cache_hit:
                    cache_hits += 1
                else:
                    cache_misses += 1
                run_status: NewsProviderRunStatus = warning_status or "completed"
                warning = (
                    record_provider_warning(warnings, warning_status, provider)
                    if warning_status is not None
                    else None
                )
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
