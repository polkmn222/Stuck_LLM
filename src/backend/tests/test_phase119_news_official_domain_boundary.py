from app.features.news_digest import service as news_digest_service


def test_news_digest_does_not_treat_suffix_spoofed_domain_as_official() -> None:
    spoofed = news_digest_service._article(
        provider="serpapi_google_web",
        query="Apple Inc AAPL latest company news earnings official business controversy",
        rank=0,
        title="Apple product roadmap update",
        url="https://fakeapple.com/product-roadmap",
        source="Fake Apple Updates",
        published_at="2026-04-29T12:00:00-04:00",
        snippet="A third-party page discusses product roadmap rumors.",
    )
    official = news_digest_service._article(
        provider="serpapi_google_web",
        query="Apple Inc AAPL latest company news earnings official business controversy",
        rank=1,
        title="Apple product roadmap update",
        url="https://www.apple.com/newsroom/product-roadmap",
        source="Apple Newsroom",
        published_at="2026-04-29T12:00:00-04:00",
        snippet="Apple published a product roadmap update.",
    )

    assert spoofed is not None
    assert official is not None
    assert spoofed.category != "official"
    assert spoofed.importance_score < official.importance_score
    assert official.category == "official"
