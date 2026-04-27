from fastapi.testclient import TestClient

from app.main import create_app


def test_ingestion_collects_global_seed_sources_for_korean_stock(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "as_of_at": "2026-04-24T09:00:00+09:00",
            "analysis_mode": "quick",
            "source_adapters": ["reddit", "us_news", "polling_sentiment", "global_macro"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["adapters_run"] == ["reddit", "us_news", "polling_sentiment", "global_macro"]
    assert body["warnings"] == ["seeded_offline_adapters_only"]
    assert {document["source_type"] for document in body["documents"]} == {
        "reddit",
        "us_news",
        "polling_sentiment",
        "global_macro",
    }
    assert all(document["url"].startswith("https://") for document in body["documents"])
    assert all(document["fetched_at"] == "2026-04-24T09:00:00+09:00" for document in body["documents"])
    assert all("seeded_offline" in document["safety_flags"] for document in body["documents"])
    assert body["documents"][0]["adapter"] == "reddit"


def test_deep_ingestion_returns_more_documents_than_quick(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    request_body = {
        "market": "KR",
        "symbol": "005930",
        "stock_name": "Samsung Electronics",
        "as_of_at": "2026-04-24T09:00:00+09:00",
        "source_adapters": ["reddit", "us_news", "polling_sentiment", "global_macro"],
    }

    quick_response = client.post(
        "/ingestion/collect",
        json={**request_body, "analysis_mode": "quick"},
    )
    deep_response = client.post(
        "/ingestion/collect",
        json={**request_body, "analysis_mode": "deep"},
    )

    assert quick_response.status_code == 201
    assert deep_response.status_code == 201
    assert deep_response.json()["document_count"] > quick_response.json()["document_count"]


def test_ingested_documents_feed_analysis_cutoff_without_future_leak(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))
    collected = client.post(
        "/ingestion/collect",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "as_of_at": "2026-04-24T09:00:00+09:00",
            "analysis_mode": "deep",
            "source_adapters": ["reddit"],
        },
    ).json()

    assert any(
        document["published_at"] > "2026-04-24T09:00:00+09:00"
        for document in collected["documents"]
    )

    analysis_response = client.post(
        "/analysis/requests",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "horizon_type": "swing",
            "analysis_mode": "deep",
            "as_of_at": "2026-04-24T09:00:00+09:00",
            "source_documents": collected["documents"],
        },
    )

    assert analysis_response.status_code == 201
    body = analysis_response.json()
    assert body["included_document_count"] == 1
    assert body["excluded_document_count"] == 1
    assert "prompt_context" not in body
    assert "Post-cutoff" not in body["summary"]
    assert body["source_documents"][1]["exclusion_reason"] == "published_after_as_of_at"


def test_ingestion_rejects_unsupported_adapter_name(tmp_path) -> None:
    client = TestClient(create_app(state_path=tmp_path / "state.json"))

    response = client.post(
        "/ingestion/collect",
        json={
            "market": "KR",
            "symbol": "005930",
            "stock_name": "Samsung Electronics",
            "as_of_at": "2026-04-24T09:00:00+09:00",
            "analysis_mode": "quick",
            "source_adapters": ["unknown_adapter"],
        },
    )

    assert response.status_code == 422
