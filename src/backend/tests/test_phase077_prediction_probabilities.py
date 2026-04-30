from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.main import create_app


class PredictionProvider:
    def __init__(self) -> None:
        self.intent_requests: List[Any] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
        return {
            "intent": "stock_analysis",
            "stock_query": "AAPL",
            "market": "US",
            "horizon_type": None,
            "analysis_mode": "quick",
            "source_hints": ["global macro"],
            "needs_follow_up": False,
            "follow_up_question": None,
        }

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        source_id = request.documents[0].id
        return LiveAnalysisOutput(
            summary="Apple evidence supports a constructive five-day setup.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=source_id,
                    stance="bullish",
                    weight=0.7,
                    summary="Macro conditions are supportive",
                    quote_excerpt="Manufacturing indicators improve.",
                )
            ],
        )


class OtherIntentPredictionProvider(PredictionProvider):
    def interpret_chat(self, request: Any) -> Dict[str, Any]:
        self.intent_requests.append(request)
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


def _clear_provider_environment(monkeypatch) -> None:
    for name in [
        "OPENAI_API_KEY",
        "OpenAI_API_Key",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "CEREBRAS_API_KEY",
        "CEREBRAS_MODEL",
        "CEREBRAS_BASE_URL",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "TAVILY_API_KEY",
        "GNEWS_API_KEY",
        "SERPAPI_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


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


def test_prediction_without_horizon_defaults_to_five_trading_day_probabilities(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    provider = PredictionProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    raw_key = "sk-phase077-prediction-secret"
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "애플 예측해줘",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"] == {
        "market": "US",
        "symbol": "AAPL",
        "stock_name": "Apple",
        "horizon_type": "swing",
        "analysis_mode": "quick",
    }
    score = body["analysis_result"]["score_result"]
    assert score["status"] == "scored"
    assert score["buy_probability"] > score["sell_probability"]
    assert round(
        score["buy_probability"] + score["hold_probability"] + score["sell_probability"],
        1,
    ) == 100.0
    assert body["messages"][-1]["meta"] == "라이브 분석"
    assert "향후 5거래일 기준 확률" in body["messages"][-1]["content"]
    assert "예상 수익률 범위" in body["messages"][-1]["content"]
    assert "하락 위험" in body["messages"][-1]["content"]
    assert "유사 이벤트 baseline" in body["messages"][-1]["content"]
    assert "매수" in body["messages"][-1]["content"]
    assert "보유" in body["messages"][-1]["content"]
    assert "매도" in body["messages"][-1]["content"]
    assert provider.intent_requests
    assert provider.analysis_requests
    assert body["analysis_result"]["source_audit"]["included_by_source_type"][
        "market_data"
    ] == 1
    market_documents = [
        document
        for document in provider.analysis_requests[0].documents
        if document.source_type == "market_data"
    ]
    assert len(market_documents) == 1
    assert "Latest market snapshot for Apple" in market_documents[0].content_text
    assert "No eligible multi-bar chart trend" in market_documents[0].content_text


def test_korean_prediction_keyword_routes_to_analysis_without_llm_intent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    provider = OtherIntentPredictionProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    raw_key = "sk-phase087-prediction-secret"
    _save_openai_credential(client, raw_key)

    response = client.post(
        "/conversations",
        json={
            "content": "애플 예측",
            "market": "KR",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    assert raw_key not in response.text
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert body["missing_inputs"] == []
    assert body["analysis_request"]["symbol"] == "AAPL"
    assert body["analysis_request"]["horizon_type"] == "swing"
    assert body["market_snapshot"] is not None
    assert body["messages"][-1]["meta"] == "라이브 분석"
    assert provider.intent_requests
    assert provider.analysis_requests
