from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatIntentOutput,
    ChatIntentProviderRequest,
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.features.ingestion import service as ingestion_service
from app.features.market_data import service as market_data_service
from app.features.market_data.schemas import MarketQuote
from app.main import create_app


class TavilySourceAnalysisProvider:
    def __init__(self) -> None:
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: ChatIntentProviderRequest) -> ChatIntentOutput:
        return ChatIntentOutput(
            intent="stock_analysis",
            stock_query="AAPL",
            market="US",
            horizon_type="swing",
            analysis_mode="quick",
            source_hints=["tavily"],
        )

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        tavily_doc = next(
            document
            for document in request.documents
            if document.source_type == "tavily_news"
        )
        return LiveAnalysisOutput(
            summary="Apple analysis using selected Tavily source.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=tavily_doc.id,
                    stance="bullish",
                    weight=0.7,
                    summary="Selected Tavily key returned Apple services demand evidence.",
                    quote_excerpt="Selected Tavily source says services demand improved.",
                )
            ],
        )


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


def test_stock_analysis_source_collection_uses_selected_external_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    selected_key = "tvly-phase149-selected-secret"
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GNEWS_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": _apple_quote() if symbol == "AAPL" else None,
        raising=False,
    )

    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 8,
    ) -> Dict[str, Any]:
        _ = headers, timeout_seconds
        assert url == "https://api.tavily.com/search"
        assert payload is not None
        assert payload["api_key"] == selected_key
        return {
            "results": [
                {
                    "title": "Apple selected Tavily source",
                    "url": "https://example.com/apple-selected-tavily",
                    "content": "Selected Tavily source says services demand improved.",
                    "published_date": "2026-05-06T12:00:00-04:00",
                }
            ]
        }

    monkeypatch.setattr(ingestion_service, "_fetch_json", fake_fetch_json)

    provider = TavilySourceAnalysisProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    llm_response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-phase149-llm-secret",
        },
    )
    assert llm_response.status_code == 200
    external_response = client.post(
        "/credentials/external/profiles",
        json={
            "credential_id": "tavily_selected",
            "label": "Selected Tavily",
            "provider": "tavily",
            "api_key": selected_key,
            "make_active": True,
        },
    )
    assert external_response.status_code == 200

    response = client.post(
        "/conversations",
        json={
            "content": "Analyze AAPL for a swing horizon using Tavily sources.",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "en",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert any(
        document["source_type"] == "tavily_news"
        and document["title"] == "Apple selected Tavily source"
        for document in body["analysis_result"]["source_documents"]
    )
    assert provider.analysis_requests
