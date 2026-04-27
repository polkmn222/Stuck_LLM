from typing import Any, Dict, List, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.ingestion.schemas import (
    CollectedSourceDocument,
    SourceAdapter,
    SourceCollectionCommand,
    SourceCollectionResponse,
)
from app.shared.state_store import LocalStateStore, State

DocumentSeed = Dict[str, Any]

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


def _collect_from_adapter(
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
    for adapter in command.source_adapters:
        documents.extend(_collect_from_adapter(adapter, command))

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
        warnings=["seeded_offline_adapters_only"],
    )

    def mutate(state: State) -> SourceCollectionResponse:
        state["source_collections"][response.collection_id] = _model_dump(response)
        return response

    return store.update(mutate)
