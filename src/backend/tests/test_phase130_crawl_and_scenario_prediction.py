from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from fastapi.testclient import TestClient

from app.features.analysis.live_provider import (
    ChatIntentOutput,
    ChatIntentProviderRequest,
    LiveAnalysisOutput,
    LiveEvidenceItem,
    LiveProviderRequest,
)
from app.features.market_data.service import get_quote
from app.features.news_digest import service as news_service
from app.features.news_digest.schemas import NewsArticle, NewsDigest, NewsSearchRun
from app.main import create_app


SEEKING_ALPHA_URL = (
    "https://seekingalpha.com/article/4897069-apple-3-reasons-this-quarter-could-reset-the-entire-story"
)
REDDIT_SEARCH_URL = "https://www.reddit.com/search/?q=apple+stock"


class ScenarioProvider:
    def __init__(self) -> None:
        self.intent_requests: List[ChatIntentProviderRequest] = []
        self.analysis_requests: List[LiveProviderRequest] = []

    def interpret_chat(self, request: ChatIntentProviderRequest) -> ChatIntentOutput:
        self.intent_requests.append(request)
        return ChatIntentOutput(
            intent="stock_analysis",
            stock_query="AAPL",
            market="US",
            horizon_type="swing",
            analysis_mode="quick",
        )

    def analyze(self, request: LiveProviderRequest) -> LiveAnalysisOutput:
        self.analysis_requests.append(request)
        news_doc = next(
            document
            for document in request.documents
            if "reset the entire story" in document.title.lower()
        )
        return LiveAnalysisOutput(
            summary="Apple analysis based on crawled headline evidence.",
            evidence_items=[
                LiveEvidenceItem(
                    source_document_id=news_doc.id,
                    stance="bullish",
                    weight=0.7,
                    summary="Crawled headline says the quarter could reset the story.",
                    quote_excerpt="3 reasons this quarter could reset the entire story",
                )
            ],
        )


def test_news_digest_crawls_seekingalpha_url_and_reddit_search_results(
    monkeypatch,
) -> None:
    quote = get_quote("US", "AAPL")
    assert quote is not None

    def fake_fetch_url_text(url: str, timeout_seconds: int = 10) -> str:
        assert timeout_seconds > 0
        assert url == SEEKING_ALPHA_URL
        return """
        <html>
          <head>
            <title>Apple: 3 Reasons This Quarter Could Reset The Entire Story</title>
            <meta property="article:published_time" content="2026-05-06T12:00:00Z" />
          </head>
          <body>
            <article>
              <p>Apple services, AI execution, and iPhone demand are the key story reset points.</p>
            </article>
          </body>
        </html>
        """

    def fake_fetch_json(
        url: str,
        *,
        headers: Dict[str, str] | None = None,
        payload: Dict[str, object] | None = None,
        timeout_seconds: int = 10,
    ) -> Dict[str, object]:
        assert "reddit.com/search.json" in url
        assert headers
        assert payload is None
        assert timeout_seconds > 0
        return {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Apple stock holders debate AI execution risk",
                            "permalink": "/r/stocks/comments/apple_ai_execution/",
                            "subreddit_name_prefixed": "r/stocks",
                            "selftext": "Retail investors are split on Apple Intelligence timing.",
                            "created_utc": 1778068800,
                        }
                    }
                ]
            }
        }

    monkeypatch.setattr(news_service, "_fetch_url_text", fake_fetch_url_text, raising=False)
    monkeypatch.setattr(news_service, "_fetch_json", fake_fetch_json)

    digest = news_service.create_news_digest(
        quote,
        requested_query=f"애플 뉴스 {SEEKING_ALPHA_URL} {REDDIT_SEARCH_URL}",
        language="ko",
        providers=(),
        important_limit=4,
    )

    titles = {article.title for article in digest.important_articles}
    assert "Apple: 3 Reasons This Quarter Could Reset The Entire Story" in titles
    assert "Apple stock holders debate AI execution risk" in titles
    assert {run.provider for run in digest.provider_runs} == {
        "web_crawl",
        "reddit_crawl",
    }


def test_prediction_uses_crawled_news_documents_and_formats_scenarios(
    tmp_path: Path,
    monkeypatch,
) -> None:
    provider = ScenarioProvider()
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", llm_analysis_provider=provider)
    )
    credential_response = client.put(
        "/credentials/llm",
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-phase130-secret",
        },
    )
    assert credential_response.status_code == 200

    def fake_digest(*args, **kwargs) -> NewsDigest:
        quote = args[0]
        return NewsDigest(
            digest_id="digest_phase130",
            status="completed",
            market=quote.market,
            symbol=quote.symbol,
            stock_name=quote.name,
            query=str(kwargs.get("requested_query") or ""),
            generated_at=quote.as_of_at,
            summary="Crawled Apple headline summary.",
            key_points=["Apple: 3 Reasons This Quarter Could Reset The Entire Story"],
            important_articles=[
                NewsArticle(
                    id="news_phase130_seekingalpha",
                    title="Apple: 3 Reasons This Quarter Could Reset The Entire Story",
                    url=SEEKING_ALPHA_URL,
                    source="Seeking Alpha",
                    published_at=quote.as_of_at,
                    snippet="Services, AI execution, and iPhone demand could reset the Apple story.",
                    provider="web_crawl",
                    query=SEEKING_ALPHA_URL,
                    rank=0,
                    category="core_business",
                    headline_ko="애플: 이번 분기가 스토리를 바꿀 수 있는 세 가지 이유",
                    summary_ko="서비스, AI 실행력, iPhone 수요가 핵심입니다.",
                    importance_score=75.0,
                    source_domain="seekingalpha.com",
                )
            ],
            additional_articles=[],
            provider_runs=[
                NewsSearchRun(
                    provider="web_crawl",
                    query=SEEKING_ALPHA_URL,
                    result_count=1,
                    status="completed",
                )
            ],
            warnings=[],
        )

    monkeypatch.setattr(
        "app.features.conversations.service.create_news_digest",
        fake_digest,
    )

    response = client.post(
        "/conversations",
        json={
            "content": f"애플 주가 예측 {SEEKING_ALPHA_URL}",
            "market": "US",
            "analysis_mode": "quick",
            "response_language": "ko",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "analysis_completed"
    assert any(
        document["title"] == "Apple: 3 Reasons This Quarter Could Reset The Entire Story"
        for document in body["analysis_result"]["source_documents"]
    )
    assert any(
        "reset the entire story" in document.title.lower()
        for document in provider.analysis_requests[0].documents
    )
    assistant_content = body["messages"][-1]["content"]
    assert "정보 기반 시나리오 분석" in assistant_content
    assert "기준 시나리오" in assistant_content
    assert "강세 시나리오" in assistant_content
    assert "약세 시나리오" in assistant_content
