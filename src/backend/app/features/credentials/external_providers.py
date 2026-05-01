import os
from dataclasses import dataclass, field
from typing import Literal, Optional

ExternalProvider = Literal["tavily", "gnews", "serpapi"]


@dataclass(frozen=True)
class ExternalProviderCredential:
    provider: ExternalProvider
    api_key: str = field(repr=False)
    key_source: Literal["environment"] = "environment"


@dataclass(frozen=True)
class NaverSearchCredential:
    client_id: str
    client_secret: str = field(repr=False)
    key_source: Literal["environment"] = "environment"


def _env_value(name: str) -> Optional[str]:
    value = os.environ.get(name, "").strip()
    return value or None


def get_external_provider_credential(
    provider: ExternalProvider,
) -> Optional[ExternalProviderCredential]:
    env_names = {
        "tavily": "TAVILY_API_KEY",
        "gnews": "GNEWS_API_KEY",
        "serpapi": "SERPAPI_API_KEY",
    }
    api_key = _env_value(env_names[provider])
    if api_key is None:
        return None
    return ExternalProviderCredential(provider=provider, api_key=api_key)


def get_naver_search_credential() -> Optional[NaverSearchCredential]:
    client_id = _env_value("NAVER_CLIENT_ID")
    client_secret = _env_value("NAVER_CLIENT_SECRET")
    if client_id is None or client_secret is None:
        return None
    return NaverSearchCredential(client_id=client_id, client_secret=client_secret)
