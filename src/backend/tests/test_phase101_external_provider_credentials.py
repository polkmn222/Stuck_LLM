from app.features.credentials.external_providers import (
    get_external_provider_credential,
    get_naver_search_credential,
)


def test_external_provider_credentials_are_loaded_from_env_without_repr_leaks(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-phase101-secret")
    monkeypatch.setenv("NAVER_CLIENT_ID", "naver-phase101-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "naver-phase101-secret")

    tavily = get_external_provider_credential("tavily")
    naver = get_naver_search_credential()

    assert tavily is not None
    assert tavily.api_key == "tavily-phase101-secret"
    assert tavily.key_source == "environment"
    assert "tavily-phase101-secret" not in repr(tavily)
    assert naver is not None
    assert naver.client_id == "naver-phase101-id"
    assert naver.client_secret == "naver-phase101-secret"
    assert "naver-phase101-secret" not in repr(naver)
