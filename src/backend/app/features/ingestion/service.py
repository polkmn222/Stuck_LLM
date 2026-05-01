import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.credentials.external_providers import (
    get_external_provider_credential,
    get_naver_search_credential,
)
from app.features.ingestion.schemas import (
    CollectedSourceDocument,
    SourceAdapter,
    SourceCollectionCommand,
    SourceCollectionResponse,
)
from app.shared.provider_status import record_provider_warning
from app.shared.state_store import LocalStateStore, State

DocumentSeed = Dict[str, Any]
DEFAULT_SOURCE_ADAPTERS: List[SourceAdapter] = [
    "naver_news",
    "tavily_news",
    "gnews_news",
    "serpapi_google_news",
    "reddit",
    "us_news",
    "global_macro",
]
HTML_TAG_RE = re.compile(r"<[^>]+>")

SEED_DOCUMENTS: Dict[SourceAdapter, List[DocumentSeed]] = {
    "reddit": [
        {
            "source_name": "Reddit r/stocks",
            "url": "https://www.reddit.com/r/stocks/comments/seed_memory_cycle/",
            "title": "Memory cycle optimism for Samsung suppliers",
            "author": "seed_reddit_user",
            "published_at": "2026-04-24T07:15:00+09:00",
            "content_text": (
                "Investors discuss stronger memory demand and AI server supply chains "
                "as supportive for Samsung Electronics."
            ),
            "language": "en",
            "relevance_score": 0.74,
        },
        {
            "source_name": "Reddit r/investing",
            "url": "https://www.reddit.com/r/investing/comments/seed_post_cutoff_samsung/",
            "title": "Post-cutoff Samsung thread reacts to later US session",
            "author": "seed_reddit_user_2",
            "published_at": "2026-04-24T12:20:00+09:00",
            "content_text": (
                "Post-cutoff discussion claims a later US session changed the view on "
                "semiconductor exporters."
            ),
            "language": "en",
            "relevance_score": 0.55,
        },
    ],
    "us_news": [
        {
            "source_name": "US Market Wire",
            "url": "https://example.com/markets/seed-semiconductor-demand",
            "title": "US chip demand supports Asian memory names",
            "author": "Seed Markets Desk",
            "published_at": "2026-04-24T06:45:00+09:00",
            "content_text": (
                "US data center orders remain firm, supporting memory demand and "
                "sector earnings recovery."
            ),
            "language": "en",
            "relevance_score": 0.81,
        },
        {
            "source_name": "Global Tech Brief",
            "url": "https://example.com/tech/seed-export-risk",
            "title": "Export controls remain a risk for global chip suppliers",
            "author": "Seed Tech Desk",
            "published_at": "2026-04-23T22:30:00+09:00",
            "content_text": "Policy risk remains a headwind for global semiconductor suppliers.",
            "language": "en",
            "relevance_score": 0.64,
        },
    ],
    "polling_sentiment": [
        {
            "source_name": "US Investor Sentiment Poll",
            "url": "https://example.com/sentiment/seed-chip-poll",
            "title": "US investor sentiment improves for AI infrastructure",
            "author": "Seed Sentiment Lab",
            "published_at": "2026-04-24T05:00:00+09:00",
            "content_text": (
                "Polling sentiment shows improved appetite for AI infrastructure and "
                "large semiconductor supply chains."
            ),
            "language": "en",
            "relevance_score": 0.69,
        },
        {
            "source_name": "Retail Positioning Survey",
            "url": "https://example.com/sentiment/seed-retail-positioning",
            "title": "Retail positioning is neutral after a fast sector rally",
            "author": "Seed Survey Desk",
            "published_at": "2026-04-23T18:00:00+09:00",
            "content_text": "Survey data suggests neutral retail positioning after recent gains.",
            "language": "en",
            "relevance_score": 0.57,
        },
    ],
    "global_macro": [
        {
            "source_name": "Global Macro Monitor",
            "url": "https://example.com/macro/seed-dollar-rates",
            "title": "Dollar and rates steady before Asian market open",
            "author": "Seed Macro Desk",
            "published_at": "2026-04-24T08:00:00+09:00",
            "content_text": (
                "The dollar and rates were steady, leaving macro conditions broadly "
                "neutral for Korean exporters."
            ),
            "language": "en",
            "relevance_score": 0.61,
        },
        {
            "source_name": "Global Growth Tracker",
            "url": "https://example.com/macro/seed-global-pmi",
            "title": "Manufacturing indicators improve in major export markets",
            "author": "Seed Macro Desk",
            "published_at": "2026-04-23T21:00:00+09:00",
            "content_text": "Manufacturing indicators improve, supporting cyclical technology demand.",
            "language": "en",
            "relevance_score": 0.66,
        },
    ],
}


class MissingSourceCredentialError(Exception):
    pass


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith(".KS"):
        return normalized[:-3]
    return normalized


def _document_limit(analysis_mode: str) -> int:
    return 1 if analysis_mode == "quick" else 2


def _clean_text(value: Any) -> str:
    return " ".join(HTML_TAG_RE.sub("", html.unescape(str(value or ""))).split())


def _normalize_published_at(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    try:
        parsed_rfc = parsedate_to_datetime(text)
        if parsed_rfc.tzinfo is not None:
            return parsed_rfc.isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed_iso = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed_iso.tzinfo is None:
        return fallback
    return parsed_iso.isoformat()


def _normalize_serpapi_news_published_at(value: Any, fallback: str) -> str:
    normalized = _normalize_published_at(value, fallback)
    if normalized != fallback:
        return normalized
    text = " ".join(str(value or "").split())
    for date_format in (
        "%b %d %Y, %I:%M:%S %p UTC%z",
        "%b %d %Y, %I:%M %p UTC%z",
    ):
        try:
            return datetime.strptime(text, date_format).isoformat()
        except ValueError:
            continue
    return fallback


def _source_query(command: SourceCollectionCommand) -> str:
    market_hint = "Korean stock" if command.market == "KR" else "US stock"
    return f"{command.stock_name} {command.symbol} {market_hint} news"


def _fetch_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 8,
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
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return cast(Dict[str, Any], json.loads(response.read().decode(charset)))


def _external_document(
    *,
    adapter: SourceAdapter,
    command: SourceCollectionCommand,
    source_name: str,
    url: str,
    title: str,
    content_text: str,
    published_at: str,
    language: str,
    relevance_score: float,
    author: Optional[str] = None,
) -> CollectedSourceDocument:
    return CollectedSourceDocument(
        id=f"source_{uuid4().hex}",
        source_type=adapter,
        source_name=source_name,
        url=url,
        title=title,
        author=author,
        published_at=published_at,
        fetched_at=command.as_of_at,
        content_text=content_text,
        language=language,
        adapter=adapter,
        relevance_score=relevance_score,
        safety_flags=["external_api", "untrusted_source_text"],
    )


def _collect_naver_news(command: SourceCollectionCommand) -> List[CollectedSourceDocument]:
    credential = get_naver_search_credential()
    if credential is None:
        raise MissingSourceCredentialError

    limit = _document_limit(command.analysis_mode)
    query = urllib.parse.urlencode(
        {
            "query": _source_query(command),
            "display": str(limit),
            "sort": "date",
        }
    )
    payload = _fetch_json(
        f"https://openapi.naver.com/v1/search/news.json?{query}",
        headers={
            "X-Naver-Client-Id": credential.client_id,
            "X-Naver-Client-Secret": credential.client_secret,
        },
    )
    documents: List[CollectedSourceDocument] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("items", []))[:limit]):
        title = _clean_text(item.get("title"))
        content_text = _clean_text(item.get("description"))
        if not title or not content_text:
            continue
        documents.append(
            _external_document(
                adapter="naver_news",
                command=command,
                source_name="Naver News",
                url=str(item.get("originallink") or item.get("link") or ""),
                title=title,
                content_text=content_text,
                published_at=_normalize_published_at(
                    item.get("pubDate"),
                    command.as_of_at,
                ),
                language="ko",
                relevance_score=round(0.9 - index * 0.04, 2),
            )
        )
    return documents


def _collect_tavily_news(command: SourceCollectionCommand) -> List[CollectedSourceDocument]:
    credential = get_external_provider_credential("tavily")
    if credential is None:
        raise MissingSourceCredentialError

    limit = _document_limit(command.analysis_mode)
    payload = _fetch_json(
        "https://api.tavily.com/search",
        payload={
            "api_key": credential.api_key,
            "query": _source_query(command),
            "search_depth": "basic",
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
        },
    )
    documents: List[CollectedSourceDocument] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("results", []))[:limit]):
        title = _clean_text(item.get("title"))
        content_text = _clean_text(item.get("content") or item.get("snippet"))
        if not title or not content_text:
            continue
        documents.append(
            _external_document(
                adapter="tavily_news",
                command=command,
                source_name="Tavily Search",
                url=str(item.get("url") or ""),
                title=title,
                content_text=content_text,
                published_at=_normalize_published_at(
                    item.get("published_date") or item.get("publishedAt"),
                    command.as_of_at,
                ),
                language="en",
                relevance_score=round(0.86 - index * 0.04, 2),
            )
        )
    return documents


def _collect_gnews_news(command: SourceCollectionCommand) -> List[CollectedSourceDocument]:
    credential = get_external_provider_credential("gnews")
    if credential is None:
        raise MissingSourceCredentialError

    limit = _document_limit(command.analysis_mode)
    query = urllib.parse.urlencode(
        {
            "q": _source_query(command),
            "lang": "en",
            "max": str(limit),
            "apikey": credential.api_key,
        }
    )
    payload = _fetch_json(f"https://gnews.io/api/v4/search?{query}")
    documents: List[CollectedSourceDocument] = []
    for index, item in enumerate(cast(List[Dict[str, Any]], payload.get("articles", []))[:limit]):
        title = _clean_text(item.get("title"))
        content_text = _clean_text(item.get("description") or item.get("content"))
        if not title or not content_text:
            continue
        source = item.get("source")
        source_name = "GNews"
        if isinstance(source, dict) and source.get("name"):
            source_name = str(source["name"])
        documents.append(
            _external_document(
                adapter="gnews_news",
                command=command,
                source_name=source_name,
                url=str(item.get("url") or ""),
                title=title,
                content_text=content_text,
                published_at=_normalize_published_at(
                    item.get("publishedAt"),
                    command.as_of_at,
                ),
                language="en",
                relevance_score=round(0.82 - index * 0.04, 2),
            )
        )
    return documents


def _serpapi_google_news_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def _serpapi_google_news_source_name(item: Dict[str, Any]) -> str:
    source = item.get("source")
    if isinstance(source, dict):
        source_name = _clean_text(source.get("name"))
    else:
        source_name = _clean_text(source)
    return source_name or "SerpApi Google News"


def _collect_serpapi_google_news(command: SourceCollectionCommand) -> List[CollectedSourceDocument]:
    credential = get_external_provider_credential("serpapi")
    if credential is None:
        raise MissingSourceCredentialError

    limit = _document_limit(command.analysis_mode)
    query = urllib.parse.urlencode(
        {
            "engine": "google_news",
            "q": _source_query(command),
            "gl": "kr" if command.market == "KR" else "us",
            "hl": "ko" if command.market == "KR" else "en",
            "api_key": credential.api_key,
        }
    )
    payload = _fetch_json(f"https://serpapi.com/search.json?{query}")
    documents: List[CollectedSourceDocument] = []
    for index, item in enumerate(_serpapi_google_news_rows(payload)[:limit]):
        title = _clean_text(item.get("title") or item.get("snippet"))
        content_text = _clean_text(
            item.get("snippet") or item.get("summary") or item.get("title")
        )
        if not title or not content_text:
            continue
        documents.append(
            _external_document(
                adapter="serpapi_google_news",
                command=command,
                source_name=_serpapi_google_news_source_name(item),
                url=str(item.get("link") or item.get("url") or ""),
                title=title,
                content_text=content_text,
                published_at=_normalize_serpapi_news_published_at(
                    item.get("date") or item.get("published_at"),
                    command.as_of_at,
                ),
                language="ko" if command.market == "KR" else "en",
                relevance_score=round(0.84 - index * 0.04, 2),
            )
        )
    return documents


def _collect_external_adapter(
    adapter: SourceAdapter,
    command: SourceCollectionCommand,
) -> List[CollectedSourceDocument]:
    if adapter == "naver_news":
        return _collect_naver_news(command)
    if adapter == "tavily_news":
        return _collect_tavily_news(command)
    if adapter == "gnews_news":
        return _collect_gnews_news(command)
    if adapter == "serpapi_google_news":
        return _collect_serpapi_google_news(command)
    return []


def _collect_seeded_adapter(
    adapter: SourceAdapter,
    command: SourceCollectionCommand,
) -> List[CollectedSourceDocument]:
    limit = _document_limit(command.analysis_mode)
    documents: List[CollectedSourceDocument] = []

    for seed in SEED_DOCUMENTS[adapter][:limit]:
        documents.append(
            CollectedSourceDocument(
                id=f"source_{uuid4().hex}",
                source_type=adapter,
                source_name=str(seed["source_name"]),
                url=str(seed["url"]),
                title=str(seed["title"]),
                author=cast(str, seed.get("author")),
                published_at=str(seed["published_at"]),
                fetched_at=command.as_of_at,
                content_text=str(seed["content_text"]),
                language=str(seed["language"]),
                adapter=adapter,
                relevance_score=float(seed["relevance_score"]),
                safety_flags=["seeded_offline", "no_network_fetch"],
            )
        )

    return documents


def collect_sources(
    store: LocalStateStore,
    command: SourceCollectionCommand,
) -> SourceCollectionResponse:
    documents: List[CollectedSourceDocument] = []
    warnings: List[str] = []
    requested_seeded_only = True

    for adapter in command.source_adapters:
        if adapter in SEED_DOCUMENTS:
            documents.extend(_collect_seeded_adapter(adapter, command))
            continue

        requested_seeded_only = False
        try:
            documents.extend(_collect_external_adapter(adapter, command))
        except MissingSourceCredentialError:
            record_provider_warning(warnings, "missing_credential", adapter)
        except AssertionError:
            raise
        except Exception:
            record_provider_warning(warnings, "provider_error", adapter)

    if requested_seeded_only:
        warnings.append("seeded_offline_adapters_only")

    response = SourceCollectionResponse(
        collection_id=f"collection_{uuid4().hex}",
        status="completed",
        market=command.market,
        symbol=_normalize_symbol(command.symbol),
        stock_name=command.stock_name,
        as_of_at=command.as_of_at,
        analysis_mode=command.analysis_mode,
        adapters_run=command.source_adapters,
        document_count=len(documents),
        documents=documents,
        warnings=warnings,
    )

    def mutate(state: State) -> SourceCollectionResponse:
        state["source_collections"][response.collection_id] = _model_dump(response)
        return response

    return store.update(mutate)
