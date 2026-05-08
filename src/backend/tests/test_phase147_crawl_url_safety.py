from __future__ import annotations

import socket
from typing import Dict, List, Tuple

import pytest

from app.features.news_digest import service as news_service


class _FakeHeaders:
    def __init__(self, content_type: str | None) -> None:
        self._content_type = content_type

    def get(self, name: str, default: str = "") -> str:
        if name.lower() == "content-type" and self._content_type is not None:
            return self._content_type
        return default


class _FakeResponse:
    def __init__(
        self,
        *,
        final_url: str,
        content_type: str | None,
        body: bytes = b"<html><title>ok</title></html>",
    ) -> None:
        self.headers = _FakeHeaders(content_type)
        self._final_url = final_url
        self._body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._final_url

    def read(self, size: int = -1) -> bytes:
        return self._body[:size] if size >= 0 else self._body


def test_safe_crawl_url_rejects_public_hostname_resolving_to_private_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(*args: object, **kwargs: object) -> List[Tuple[object, ...]]:
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("127.0.0.1", 443),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    assert news_service._safe_crawl_url("https://attacker.example/article") is None


def test_safe_crawl_url_rejects_malformed_port() -> None:
    assert news_service._safe_crawl_url("https://public.example:bad/article") is None


def test_fetch_url_text_rejects_redirect_target_resolving_to_private_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolved: Dict[str, str] = {
        "public.example": "93.184.216.34",
        "metadata.example": "169.254.169.254",
    }

    def fake_getaddrinfo(host: str, *args: object, **kwargs: object) -> List[Tuple[object, ...]]:
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                (resolved[str(host)], 443),
            )
        ]

    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(
            final_url="https://metadata.example/latest/meta-data",
            content_type="text/html",
        )

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(news_service.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(news_service.NewsProviderError, match="Crawl redirect target"):
        news_service._fetch_url_text("https://public.example/article")


def test_fetch_url_text_rejects_unsupported_response_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(*args: object, **kwargs: object) -> List[Tuple[object, ...]]:
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", 443),
            )
        ]

    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(
            final_url="https://public.example/report.pdf",
            content_type="application/pdf",
            body=b"%PDF-1.7",
        )

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(news_service.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(news_service.NewsProviderError, match="response type"):
        news_service._fetch_url_text("https://public.example/report.pdf")
