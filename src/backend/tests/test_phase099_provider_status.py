from app.shared.provider_status import provider_warning, record_provider_warning


def test_provider_warning_helpers_keep_missing_credentials_and_provider_errors_consistent() -> None:
    warnings: list[str] = []

    assert provider_warning("completed", "tavily_news") is None
    assert provider_warning("missing_credential", "tavily_news") == "missing_credential:tavily_news"
    assert provider_warning("provider_error", "gnews_news") == "provider_error:gnews_news"

    assert record_provider_warning(warnings, "missing_credential", "tavily_news") == (
        "missing_credential:tavily_news"
    )
    assert record_provider_warning(warnings, "missing_credential", "tavily_news") == (
        "missing_credential:tavily_news"
    )
    assert warnings == ["missing_credential:tavily_news"]
