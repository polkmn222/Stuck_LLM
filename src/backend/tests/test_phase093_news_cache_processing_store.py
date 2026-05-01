from pathlib import Path
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from app.features.market_data.schemas import MarketQuote
from app.features.news_digest import service as news_digest_service
from app.features.processing_cache.service import cache_key
from app.main import create_app
from app.shared.state_store import LocalStateStore


def _quote(symbol: str = "AAPL", name: str = "Apple Inc") -> MarketQuote:
    return MarketQuote(
        market="US",
        symbol=symbol,
        name=name,
        exchange="NASDAQ",
        currency="USD",
        last_price=0.0,
        as_of_at="2026-04-29T16:00:00-04:00",
        source="sp500_directory_metadata",
    )


def test_news_provider_results_are_cached_and_processing_runs_are_recorded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store = LocalStateStore(tmp_path / "state.json")
    call_count = 0

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        nonlocal call_count
        _ = url, headers, timeout_seconds
        call_count += 1
        query = str(payload["query"] if payload is not None else "")
        return {
            "results": [
                {
                    "title": f"Cached article for {query}",
                    "url": f"https://example.com/{call_count}",
                    "content": "Provider payload should be cached without credentials.",
                    "published_date": "2026-04-29T13:00:00-04:00",
                }
            ]
        }

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase093-secret")
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)

    queries = news_digest_service._build_news_queries(_quote(), "애플 뉴스")
    first = news_digest_service.create_news_digest(
        _quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=("tavily_news",),
        store=store,
    )
    first_call_count = call_count
    second = news_digest_service.create_news_digest(
        _quote(),
        requested_query="애플 뉴스",
        language="ko",
        providers=("tavily_news",),
        store=store,
    )

    state = store.read()
    serialized_state = str(state)

    assert first.status == "completed"
    assert second.status == "completed"
    assert first_call_count == len(queries)
    assert call_count == first_call_count
    assert len(state["kv_cache"]) == len(queries)
    assert len(state["news_processing_runs"]) == 2
    assert "tavily-phase093-secret" not in serialized_state
    assert any(run["cache_hits"] == len(queries) for run in state["news_processing_runs"].values())


def test_processing_cache_status_and_invalidation_route(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    store = LocalStateStore(state_path)
    key = cache_key("news_digest_provider", {"query": "AAPL news", "provider": "tavily_news"})
    store.update(
        lambda state: state["kv_cache"].update(
            {
                key: {
                    "namespace": "news_digest_provider",
                    "key": key,
                    "created_at": "2026-04-29T00:00:00Z",
                    "expires_at": "2026-05-02T00:00:00Z",
                    "payload": {"articles": []},
                }
            }
        )
    )
    client = TestClient(create_app(state_path=state_path))

    status_response = client.get("/processing-cache/status")

    assert status_response.status_code == 200
    assert status_response.json()["kv_cache"]["total_entries"] == 1
    assert status_response.json()["kv_cache"]["namespaces"]["news_digest_provider"] == 1

    invalidate_response = client.post("/processing-cache/invalidate", json={"key": key})

    assert invalidate_response.status_code == 200
    assert invalidate_response.json() == {"key": key, "removed": True}
    assert store.read()["kv_cache"] == {}
