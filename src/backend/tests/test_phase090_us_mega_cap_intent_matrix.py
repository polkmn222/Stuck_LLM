import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatCompletionProviderRequest,
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.features.market_data import service as market_data_service
from app.features.news_digest import service as news_digest_service
from app.main import create_app


MEGA_CAPS = (
    ("애플", "AAPL", "Apple Inc", 270.71),
    ("구글", "GOOG", "Alphabet Inc Class C", 348.0),
    ("엔비디아", "NVDA", "NVIDIA Corp", 910.25),
    ("테슬라", "TSLA", "Tesla Inc", 242.80),
)
MEGA_CAPS_BY_SYMBOL = {
    symbol: (korean_name, company_name, price)
    for korean_name, symbol, company_name, price in MEGA_CAPS
}


class OtherIntentMatrixProvider:
    def __init__(self) -> None:
        self.analysis_requests: List[LiveProviderRequest] = []
        self.completion_requests: List[ChatCompletionProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        return {
            "intent": "other",
            "stock_query": None,
            "market": None,
            "horizon_type": None,
            "analysis_mode": None,
            "source_hints": [],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def complete_chat(self, request: ChatCompletionProviderRequest) -> str:
        self.completion_requests.append(request)
        return "뉴스 요약 테스트"

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="Mega-cap matrix evidence supports a five-day setup.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.65,
                    summary="Quote and chart evidence are available.",
                    quote_excerpt="Latest market snapshot and graph bars are present.",
                )
            ],
        )


def _quote_payload(symbol: str, company_name: str, price: float) -> Dict[str, Any]:
    return {
        "search_metadata": {"status": "Success"},
        "summary": {
            "title": company_name,
            "stock": symbol,
            "exchange": "NASDAQ",
            "extracted_price": price,
            "currency": "USD",
            "price_movement": {
                "percentage": 1.2,
                "value": 2.0,
                "movement": "Up",
            },
            "date": "Apr 29 2026, 04:00:00 PM UTC-04:00",
        },
        "graph": [
            {
                "price": price - 2.0,
                "date": "Apr 29 2026, 09:30 AM UTC-04:00",
                "volume": 1000,
            },
            {
                "price": price,
                "date": "Apr 29 2026, 04:00 PM UTC-04:00",
                "volume": 2000,
            },
        ],
    }


def _symbol_from_google_finance_query(query: str) -> Optional[str]:
    if query in {"USD-KRW", "USD/KRW", "USDKRW"}:
        return "USD-KRW"
    first, _, second = query.partition(":")
    symbol = second if first == "NASDAQ" else first
    return symbol if symbol in MEGA_CAPS_BY_SYMBOL else None


def _fake_serpapi_google_finance(
    query: str,
    api_key: str,
    *,
    window: str = "1D",
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    _ = window, timeout_seconds
    assert api_key == "serpapi-phase090-secret"
    symbol = _symbol_from_google_finance_query(query)
    if symbol == "USD-KRW":
        return _quote_payload("USD-KRW", "USD / KRW", 1390.0)
    if symbol is None:
        raise AssertionError(f"Unexpected Google Finance query: {query}")
    _, company_name, price = MEGA_CAPS_BY_SYMBOL[symbol]
    return _quote_payload(symbol, company_name, price)


def _request_query_from_url(url: str) -> str:
    import urllib.parse

    parsed = urllib.parse.urlsplit(url)
    query_items = urllib.parse.parse_qs(parsed.query)
    return query_items.get("q", query_items.get("query", [""]))[0]


def _symbol_from_news_query(query: str) -> str:
    return next(
        (symbol for symbol in MEGA_CAPS_BY_SYMBOL if symbol in query),
        "AAPL",
    )


def _fake_news_fetch(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    _ = headers, timeout_seconds
    query = str(payload.get("query") if payload is not None else _request_query_from_url(url))
    symbol = _symbol_from_news_query(query)
    _, company_name, _price = MEGA_CAPS_BY_SYMBOL[symbol]
    slug = symbol.lower()
    if payload is not None:
        return {
            "results": [
                {
                    "title": f"{company_name} earnings and AI strategy update",
                    "url": f"https://example.com/{slug}-news",
                    "content": f"{company_name} latest business news.",
                    "published_date": "2026-04-29T13:00:00-04:00",
                }
            ]
        }
    if "gnews.io" in url:
        return {
            "articles": [
                {
                    "title": f"{company_name} analyst update",
                    "url": f"https://example.com/{slug}-analyst",
                    "description": f"{company_name} analyst context.",
                    "publishedAt": "2026-04-29T12:00:00-04:00",
                    "source": {"name": "GNews"},
                }
            ]
        }
    if "engine=google_news" in url:
        return {
            "news_results": [
                {
                    "title": f"{company_name} product news",
                    "link": f"https://example.com/{slug}-product",
                    "source": "Serp News",
                    "date": "Apr 29 2026, 02:30 PM UTC-04:00",
                    "snippet": f"{company_name} product context.",
                }
            ]
        }
    if "engine=google" in url:
        return {
            "organic_results": [
                {
                    "title": f"{company_name} market reaction",
                    "link": f"https://example.com/{slug}-market",
                    "source": "Example",
                    "date": "Apr 29, 2026",
                    "snippet": f"{company_name} market reaction.",
                }
            ]
        }
    raise AssertionError(f"Unexpected news URL: {url}")


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


def _configure_matrix_environment(monkeypatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "serpapi-phase090-secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase090-secret")
    monkeypatch.setenv("GNEWS_API_KEY", "gnews-phase090-secret")
    monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
    monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(
        market_data_service,
        "_search_serpapi_google_finance",
        _fake_serpapi_google_finance,
        raising=False,
    )
    monkeypatch.setattr(news_digest_service, "_fetch_json", _fake_news_fetch)


def test_us_mega_cap_korean_news_chart_and_prediction_matrix(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _configure_matrix_environment(monkeypatch)
    raw_key = "sk-phase090-matrix-secret"
    provider = OtherIntentMatrixProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    _save_openai_credential(client, raw_key)

    for korean_name, expected_symbol, _company_name, _price in MEGA_CAPS:
        news_response = client.post(
            "/conversations",
            json={
                "content": f"{korean_name} 뉴스",
                "market": "KR",
                "analysis_mode": "quick",
                "response_language": "ko",
            },
        )
        news_body = news_response.json()
        assert news_response.status_code == 201
        assert news_body["status"] == "news_digest"
        assert news_body["news_digest"]["symbol"] == expected_symbol
        assert news_body["analysis_request"] is None
        assert news_body["missing_inputs"] == []
        assert any(
            expected_symbol in run["query"]
            for run in news_body["news_digest"]["provider_runs"]
        )
        assert raw_key not in news_response.text
        assert os.environ["SERPAPI_API_KEY"] not in news_response.text

        chart_response = client.post(
            "/conversations",
            json={
                "content": f"{korean_name} 주가 차트",
                "market": "KR",
                "analysis_mode": "quick",
                "response_language": "ko",
            },
        )
        chart_body = chart_response.json()
        assert chart_response.status_code == 201
        assert chart_body["status"] == "market_snapshot"
        assert chart_body["market_snapshot"]["market"] == "US"
        assert chart_body["market_snapshot"]["symbol"] == expected_symbol
        assert chart_body["market_snapshot"]["currency"] == "USD"
        assert chart_body["market_snapshot"]["chart_window"] == "1D"
        assert len(chart_body["market_snapshot"]["chart_bars"]) == 2
        assert chart_body["analysis_request"] is None
        assert raw_key not in chart_response.text
        assert os.environ["SERPAPI_API_KEY"] not in chart_response.text

        prediction_response = client.post(
            "/conversations",
            json={
                "content": f"{korean_name} 예측",
                "market": "KR",
                "analysis_mode": "quick",
                "response_language": "ko",
            },
        )
        prediction_body = prediction_response.json()
        assert prediction_response.status_code == 201
        assert prediction_body["status"] == "analysis_completed"
        assert prediction_body["missing_inputs"] == []
        assert prediction_body["analysis_request"]["market"] == "US"
        assert prediction_body["analysis_request"]["symbol"] == expected_symbol
        assert prediction_body["analysis_request"]["horizon_type"] == "swing"
        assert prediction_body["analysis_result"]["score_result"]["status"] == "scored"
        assert prediction_body["analysis_result"]["source_audit"]["included_by_source_type"][
            "market_data"
        ] == 1
        assert raw_key not in prediction_response.text
        assert os.environ["SERPAPI_API_KEY"] not in prediction_response.text

    assert len(provider.analysis_requests) == len(MEGA_CAPS)
