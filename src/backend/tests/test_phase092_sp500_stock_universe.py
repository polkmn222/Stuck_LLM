from pathlib import Path
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from app.features.market_data import service as market_data_service
from app.features.news_digest import service as news_digest_service
from app.main import create_app


def test_sp500_universe_exposes_all_symbols_and_metadata_quotes() -> None:
    companies = market_data_service.list_sp500_companies()
    symbols = {company.symbol for company in companies}

    assert len(companies) >= 500
    assert {"AAPL", "GOOG", "NVDA", "TSLA", "JPM", "XOM", "LLY", "WMT"}.issubset(symbols)

    microsoft = market_data_service.resolve_sp500_metadata_quote_from_text("마이크로소프트 뉴스")
    jpmorgan = market_data_service.resolve_sp500_metadata_quote_from_text("JPMorgan Chase 뉴스")

    assert microsoft is not None
    assert microsoft.symbol == "MSFT"
    assert microsoft.source == "sp500_directory_metadata"
    assert microsoft.currency == "USD"
    assert jpmorgan is not None
    assert jpmorgan.symbol == "JPM"
    assert jpmorgan.market == "US"


def test_sp500_google_finance_candidates_are_available_for_representative_symbols() -> None:
    for symbol in ("AAPL", "GOOG", "NVDA", "TSLA", "JPM", "XOM", "LLY", "WMT"):
        candidates = market_data_service.google_finance_query_candidates(symbol)

        assert symbol in candidates[-1]
        assert any(candidate.startswith(f"{symbol}:") for candidate in candidates)
        assert any("NASDAQ" in candidate or "NYSE" in candidate for candidate in candidates)


def test_sp500_metadata_quote_supports_conversation_news_without_live_quote(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_fetch_json(
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, Any]:
        _ = url, headers, timeout_seconds
        query = str(payload["query"] if payload is not None else "")
        assert "Microsoft" in query
        assert "MSFT" in query
        return {
            "results": [
                {
                    "title": "Microsoft cloud and AI strategy update",
                    "url": "https://example.com/msft-ai",
                    "content": "Microsoft news can be collected from S&P 500 metadata.",
                    "published_date": "2026-04-29T13:00:00-04:00",
                }
            ]
        }

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase092")
    for name in ("GNEWS_API_KEY", "SERPAPI_API_KEY", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(news_digest_service, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_serpapi_google_finance",
        lambda symbol, window="1D": None,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_quote_from_finance_data_reader",
        lambda market, symbol: None,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/conversations",
        json={
            "content": "마이크로소프트 뉴스",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    body = response.json()

    assert response.status_code == 201
    assert body["status"] == "news_digest"
    assert body["news_digest"]["symbol"] == "MSFT"
    assert body["news_digest"]["stock_name"] == "Microsoft"
    assert body["analysis_request"] is None
    assert "tavily-phase092" not in response.text
