import json
import urllib.parse

from fastapi.testclient import TestClient

from app.features.credentials.service import get_llm_credential_secret
from app.features.ingestion import service as ingestion_service
from app.features.market_data import service as market_data_service
from app.main import create_app


class FakeFinanceFrame:
    def __init__(self, records):
        self._records = records

    def reset_index(self):
        return self

    def to_dict(self, orient):
        assert orient == "records"
        return self._records


def test_finance_data_reader_quote_includes_snapshot_and_chart(monkeypatch, tmp_path) -> None:
    records = [
        {
            "Date": "2026-04-22",
            "Open": 70100,
            "High": 71300,
            "Low": 69800,
            "Close": 71000,
            "Volume": 12200000,
        },
        {
            "Date": "2026-04-23",
            "Open": 71200,
            "High": 72400,
            "Low": 70700,
            "Close": 72000,
            "Volume": 14100000,
        },
        {
            "Date": "2026-04-24",
            "Open": 71800,
            "High": 72600,
            "Low": 71000,
            "Close": 72400,
            "Volume": 15500000,
            "Change": 0.0056,
        },
    ]

    def fake_read_finance_data(symbol, start_date, end_date):
        assert symbol == "005930"
        assert start_date <= end_date
        return FakeFinanceFrame(records)

    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        fake_read_finance_data,
        raising=False,
    )

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.get("/market-data/quotes/KR/005930")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "finance_data_reader"
    assert body["last_price"] == 72400.0
    assert body["previous_close"] == 72000.0
    assert body["change_pct"] == 0.56
    assert body["chart_bars"][-1] == {
        "timestamp": "2026-04-24T00:00:00+09:00",
        "open": 71800.0,
        "high": 72600.0,
        "low": 71000.0,
        "close": 72400.0,
        "volume": 15500000.0,
    }


def test_ingestion_collects_naver_tavily_and_gnews_without_leaking_keys(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("NAVER_CLIENT_ID", "naver-client")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "naver-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-secret")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-secret")

    def fake_fetch_json(url, *, headers=None, payload=None, timeout_seconds=8):
        assert timeout_seconds == 8
        if "openapi.naver.com" in url:
            assert headers["X-Naver-Client-Id"] == "naver-client"
            assert headers["X-Naver-Client-Secret"] == "naver-secret"
            return {
                "items": [
                    {
                        "title": "<b>Samsung</b> memory demand improves",
                        "originallink": "https://news.example.com/samsung-memory",
                        "description": "AI server orders support <b>memory</b> recovery.",
                        "pubDate": "Fri, 24 Apr 2026 09:20:00 +0900",
                    }
                ]
            }
        if "api.tavily.com" in url:
            assert payload["api_key"] == "tavily-secret"
            return {
                "results": [
                    {
                        "title": "US chip demand supports Asian suppliers",
                        "url": "https://search.example.com/chip-demand",
                        "content": "US data center demand remains strong for memory makers.",
                        "published_date": "2026-04-24T00:10:00Z",
                    }
                ]
            }
        if "gnews.io" in url:
            assert "apikey=gnews-secret" in url
            return {
                "articles": [
                    {
                        "title": "Global tech shares rise",
                        "url": "https://gnews.example.com/global-tech",
                        "description": "Global technology shares rise on earnings growth.",
                        "publishedAt": "2026-04-23T22:30:00Z",
                        "source": {"name": "GNews Wire"},
                    }
                ]
            }
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(
        ingestion_service,
        "_fetch_json",
        fake_fetch_json,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "as_of_at": "2026-04-24T10:00:00+09:00",
            "analysis_mode": "quick",
            "source_adapters": ["naver_news", "tavily_news", "gnews_news"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["warnings"] == []
    assert body["document_count"] == 3
    assert {document["source_type"] for document in body["documents"]} == {
        "naver_news",
        "tavily_news",
        "gnews_news",
    }
    assert body["documents"][0]["title"] == "Samsung memory demand improves"
    assert all("external_api" in document["safety_flags"] for document in body["documents"])
    assert all(
        "untrusted_source_text" in document["safety_flags"]
        for document in body["documents"]
    )

    serialized = json.dumps(body)
    assert "naver-secret" not in serialized
    assert "tavily-secret" not in serialized
    assert "gnews-secret" not in serialized


def test_ingestion_collects_serpapi_google_news_without_leaking_key(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-news-secret")

    def fake_fetch_json(url, *, headers=None, payload=None, timeout_seconds=8):
        assert headers is None
        assert payload is None
        assert timeout_seconds == 8
        parsed_url = urllib.parse.urlparse(url)
        assert parsed_url.netloc == "serpapi.com"
        assert parsed_url.path == "/search.json"
        query = urllib.parse.parse_qs(parsed_url.query)
        assert query["engine"] == ["google_news"]
        assert query["api_key"] == ["serpapi-news-secret"]
        assert query["q"] == ["Apple AAPL US stock news"]
        return {
            "news_results": [
                {
                    "title": "Apple demand improves",
                    "source": {"name": "Market Wire"},
                    "date": "Apr 28 2026, 01:15 PM UTC-04:00",
                    "link": "https://news.example.com/apple-demand",
                    "snippet": "Supplier checks pointed to stronger iPhone demand.",
                },
                {
                    "title": "Apple earnings topic",
                    "stories": [
                        {
                            "title": "Services growth supports Apple margin",
                            "source": "Finance Desk",
                            "date": "Apr 28 2026, 02:30 PM UTC-04:00",
                            "link": "https://news.example.com/apple-services",
                            "snippet": "Services revenue helped margins hold up.",
                        }
                    ],
                },
            ]
        }

    monkeypatch.setattr(
        ingestion_service,
        "_fetch_json",
        fake_fetch_json,
        raising=False,
    )
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "US",
            "symbol": "AAPL",
            "stock_name": "Apple",
            "as_of_at": "2026-04-28T16:00:00-04:00",
            "analysis_mode": "deep",
            "source_adapters": ["serpapi_google_news"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["warnings"] == []
    assert body["document_count"] == 2
    assert body["adapters_run"] == ["serpapi_google_news"]
    assert [document["title"] for document in body["documents"]] == [
        "Apple demand improves",
        "Services growth supports Apple margin",
    ]
    assert body["documents"][0]["source_type"] == "serpapi_google_news"
    assert body["documents"][0]["source_name"] == "Market Wire"
    assert body["documents"][0]["published_at"] == "2026-04-28T13:15:00-04:00"
    assert body["documents"][1]["source_name"] == "Finance Desk"
    assert body["documents"][1]["published_at"] == "2026-04-28T14:30:00-04:00"
    assert all("external_api" in document["safety_flags"] for document in body["documents"])
    assert all(
        "untrusted_source_text" in document["safety_flags"]
        for document in body["documents"]
    )
    assert "serpapi-news-secret" not in json.dumps(body)


def test_ingestion_missing_serpapi_google_news_key_returns_safe_warning(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "US",
            "symbol": "AAPL",
            "stock_name": "Apple",
            "as_of_at": "2026-04-28T16:00:00-04:00",
            "analysis_mode": "quick",
            "source_adapters": ["serpapi_google_news"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_count"] == 0
    assert body["warnings"] == ["missing_credential:serpapi_google_news"]
    assert "secret" not in json.dumps(body).lower()


def test_ingestion_missing_external_credentials_returns_safe_warnings(
    monkeypatch,
    tmp_path,
) -> None:
    for name in [
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "as_of_at": "2026-04-24T10:00:00+09:00",
            "analysis_mode": "quick",
            "source_adapters": ["naver_news", "tavily_news", "gnews_news"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_count"] == 0
    assert body["warnings"] == [
        "missing_credential:naver_news",
        "missing_credential:tavily_news",
        "missing_credential:gnews_news",
    ]
    assert "secret" not in json.dumps(body).lower()


def test_live_llm_secret_ignores_openai_environment_key_without_saved_user_key(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("OpenAI_API_Key", "sk-env-phase019-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-env-phase019")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    state_path = tmp_path / "state.json"
    app = create_app(state_path=state_path)

    secret = get_llm_credential_secret(
        app.state.local_store,
        app.state.credential_cipher,
    )

    assert secret is None
    assert not state_path.exists() or "sk-env-phase019-secret" not in state_path.read_text()
