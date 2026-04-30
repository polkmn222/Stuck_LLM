import json

from fastapi.testclient import TestClient

from app.features.market_data import service as market_data_service
from app.main import create_app


def test_serpapi_google_finance_quote_is_preferred_for_us_when_key_is_configured(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase022-secret")

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise AssertionError("SerpApi should be tried before FinanceDataReader for US quotes")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "GOOGL:NASDAQ"
        assert api_key == "serpapi-phase022-secret"
        assert window == "1D"
        assert timeout_seconds == 10
        return {
            "search_metadata": {"status": "Success"},
            "summary": {
                "title": "Alphabet Inc Class A",
                "stock": "GOOGL",
                "exchange": "NASDAQ",
                "extracted_price": 176.77,
                "currency": "USD",
                "price_movement": {
                    "percentage": 1.1960682,
                    "value": 2.0999982,
                    "movement": "Up",
                },
                "date": "Apr 27 2026, 04:00:00 PM UTC-04:00",
            },
            "knowledge_graph": {
                "key_stats": {
                    "stats": [
                        {"label": "Previous close", "value": "$174.67"},
                    ]
                }
            },
            "graph": [
                {
                    "price": 174.95,
                    "currency": "USD",
                    "date": "Apr 27 2026, 09:30 AM UTC-04:00",
                    "volume": 7413,
                },
                {
                    "price": 176.77,
                    "currency": "USD",
                    "date": "Apr 27 2026, 04:00 PM UTC-04:00",
                    "volume": 155326,
                },
            ],
        }

    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/GOOGL")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "serpapi_google_finance"
    assert body["market"] == "US"
    assert body["symbol"] == "GOOGL"
    assert body["name"] == "Alphabet Inc Class A"
    assert body["exchange"] == "NASDAQ"
    assert body["currency"] == "USD"
    assert body["last_price"] == 176.77
    assert body["previous_close"] == 174.67
    assert body["change_pct"] == 1.2
    assert body["as_of_at"] == "2026-04-27T16:00:00-04:00"
    assert body["chart_bars"] == [
        {
            "timestamp": "2026-04-27T09:30:00-04:00",
            "open": 174.95,
            "high": 174.95,
            "low": 174.95,
            "close": 174.95,
            "volume": 7413.0,
        },
        {
            "timestamp": "2026-04-27T16:00:00-04:00",
            "open": 176.77,
            "high": 176.77,
            "low": 176.77,
            "close": 176.77,
            "volume": 155326.0,
        },
    ]
    assert "serpapi-phase022-secret" not in json.dumps(body)


def test_us_quote_endpoint_passes_requested_chart_window_to_serpapi(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase050-secret")

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise AssertionError("SerpApi should provide the requested US window")

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert query == "AAPL:NASDAQ"
        assert api_key == "serpapi-phase050-secret"
        assert window == "5D"
        assert timeout_seconds == 10
        return {
            "search_metadata": {"status": "Success"},
            "summary": {
                "title": "Apple Inc",
                "stock": "AAPL",
                "exchange": "NASDAQ",
                "extracted_price": 270.71,
                "currency": "USD",
                "date": "Apr 29 2026, 04:00:00 PM UTC-04:00",
            },
            "graph": [
                {
                    "price": 268.0,
                    "date": "Apr 24 2026, 04:00 PM UTC-04:00",
                    "volume": 100,
                },
                {
                    "price": 270.71,
                    "date": "Apr 29 2026, 04:00 PM UTC-04:00",
                    "volume": 200,
                },
            ],
        }

    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/AAPL?window=5D")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "serpapi_google_finance"
    assert body["symbol"] == "AAPL"
    assert body["chart_window"] == "5D"
    assert body["chart_bars"][0]["close"] == 268.0
    assert body["chart_bars"][-1]["close"] == 270.71
    assert "serpapi-phase050-secret" not in json.dumps(body)


def test_serpapi_google_finance_errors_fall_back_to_seeded_quote_without_leaking_key(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase022-secret")

    def fail_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        raise market_data_service.MarketDataProviderError(
            "SerpApi Google Finance request failed."
        )

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise market_data_service.MarketDataProviderError(
            "FinanceDataReader request failed."
        )

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fail_serpapi_search,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/AAPL")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "seeded_local_fixture"
    assert body["symbol"] == "AAPL"
    assert "serpapi-phase022-secret" not in json.dumps(body)


def test_serpapi_google_finance_is_not_called_without_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    def fail_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        raise AssertionError("SerpApi should not be called without SERPAPI_API_KEY")

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise market_data_service.MarketDataProviderError(
            "FinanceDataReader request failed."
        )

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fail_serpapi_search,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/AAPL")

    assert response.status_code == 200
    assert response.json()["source"] == "seeded_local_fixture"


def test_serpapi_google_finance_tries_exchange_candidates_until_quote_found(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase046-secret")
    attempted_queries = []

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert api_key == "serpapi-phase046-secret"
        attempted_queries.append(query)
        if query == "ACME:NASDAQ":
            return {
                "search_metadata": {"status": "Success"},
                "summary": {"title": "No quote data yet"},
            }
        if query == "ACME:NYSE":
            return {
                "search_metadata": {"status": "Success"},
                "summary": {
                    "title": "Acme Industrial",
                    "stock": "ACME",
                    "exchange": "NYSE",
                    "extracted_price": 42.25,
                    "currency": "USD",
                    "date": "Apr 28 2026, 04:00:00 PM UTC-04:00",
                },
                "graph": [
                    {
                        "price": 41.5,
                        "date": "Apr 28 2026, 09:30 AM UTC-04:00",
                        "volume": 100,
                    },
                    {
                        "price": 42.25,
                        "date": "Apr 28 2026, 04:00 PM UTC-04:00",
                        "volume": 200,
                    },
                ],
            }
        raise AssertionError(f"unexpected query: {query}")

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise AssertionError("A later SerpApi candidate should provide the quote")

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/ACME")

    assert response.status_code == 200
    body = response.json()
    assert attempted_queries == ["ACME:NASDAQ", "ACME:NYSE"]
    assert body["source"] == "serpapi_google_finance"
    assert body["symbol"] == "ACME"
    assert body["exchange"] == "NYSE"
    assert body["last_price"] == 42.25
    assert "serpapi-phase046-secret" not in json.dumps(body)


def test_colon_us_quote_tries_reversed_google_finance_exchange_candidate(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase050-secret")
    attempted_queries = []

    def fake_serpapi_search(query, api_key, *, window="1D", timeout_seconds=10):
        assert api_key == "serpapi-phase050-secret"
        attempted_queries.append(query)
        if query in {"AAPL:NASDAQ", "AAPL"}:
            return {
                "search_metadata": {"status": "Success"},
                "summary": {"title": "No quote data yet"},
            }
        if query == "NASDAQ:AAPL":
            return {
                "search_metadata": {"status": "Success"},
                "summary": {
                    "title": "Apple Inc",
                    "stock": "AAPL",
                    "exchange": "NASDAQ",
                    "extracted_price": 270.71,
                    "currency": "USD",
                    "date": "Apr 29 2026, 04:00:00 PM UTC-04:00",
                },
                "graph": [
                    {
                        "price": 268.0,
                        "date": "Apr 29 2026, 09:30 AM UTC-04:00",
                        "volume": 100,
                    },
                    {
                        "price": 270.71,
                        "date": "Apr 29 2026, 04:00 PM UTC-04:00",
                        "volume": 200,
                    },
                ],
            }
        raise AssertionError(f"unexpected query: {query}")

    def fail_finance_data_reader(symbol, start_date, end_date):
        raise market_data_service.MarketDataProviderError(
            "FinanceDataReader request failed."
        )

    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        fake_serpapi_search,
        raising=False,
    )
    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fail_finance_data_reader,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/US/AAPL:NASDAQ")

    assert response.status_code == 200
    body = response.json()
    assert attempted_queries == ["AAPL:NASDAQ", "NASDAQ:AAPL"]
    assert body["source"] == "serpapi_google_finance"
    assert body["symbol"] == "AAPL"
    assert body["exchange"] == "NASDAQ"
    assert body["last_price"] == 270.71
    assert "serpapi-phase050-secret" not in json.dumps(body)
