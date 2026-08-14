"""Tests for the link unfurling service.

Covers HTML metadata extraction, SSRF safety checks, and the caching
behaviour of ``unfurl_url``. Async code is driven via ``asyncio.run`` since
the project does not use an asyncio pytest plugin.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Generator
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ring.link_unfurl.service import (
    LinkUnfurlError,
    UnsafeURLError,
    assert_url_is_safe,
    clear_link_preview_cache,
    extract_link_preview,
    unfurl_url,
)


def _mock_async_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> Callable[..., httpx.AsyncClient]:
    """Build a drop-in ``httpx.AsyncClient`` factory backed by a mock.

    The real client is constructed so redirect/stream/read behaviour is
    exercised, but requests are served by ``handler`` instead of the network.
    """
    real_async_client = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return real_async_client(
            *args, transport=httpx.MockTransport(handler), **kwargs
        )

    return factory


HTML_FULL = """
<html><head>
<title>Fallback Title</title>
<meta property="og:title" content="OG Title">
<meta property="og:description" content="OG Description">
<meta property="og:image" content="/img/preview.png">
<meta property="og:site_name" content="Example Site">
<link rel="icon" href="/favicon-32.png">
</head><body>hello</body></html>
"""

HTML_TWITTER_FALLBACK = """
<html><head>
<title>Page Title</title>
<meta name="twitter:title" content="TW Title">
<meta name="twitter:description" content="TW Desc">
<meta name="twitter:image" content="https://cdn.example.com/x.jpg">
</head><body></body></html>
"""

HTML_TITLE_ONLY = (
    "<html><head><title>Just Title</title>"
    "<meta name='description' content='Plain Desc'>"
    "</head><body></body></html>"
)


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    clear_link_preview_cache()
    yield
    clear_link_preview_cache()


class TestExtractLinkPreview:
    def test_prefers_open_graph_and_absolutizes_urls(self) -> None:
        preview = extract_link_preview(
            HTML_FULL,
            base_url="https://example.com/a/page",
            requested_url="https://example.com/a/page",
        )
        assert preview.title == "OG Title"
        assert preview.description == "OG Description"
        assert preview.image_url == "https://example.com/img/preview.png"
        assert preview.site_name == "Example Site"
        assert preview.favicon_url == "https://example.com/favicon-32.png"
        assert preview.url == "https://example.com/a/page"
        assert preview.resolved_url == "https://example.com/a/page"

    def test_falls_back_to_twitter_and_hostname(self) -> None:
        preview = extract_link_preview(
            HTML_TWITTER_FALLBACK,
            base_url="https://sub.example.com/a/b",
            requested_url="https://sub.example.com/a/b",
        )
        assert preview.title == "TW Title"
        assert preview.description == "TW Desc"
        # Already-absolute image URLs are preserved.
        assert preview.image_url == "https://cdn.example.com/x.jpg"
        # No og:site_name -> hostname of the resolved URL.
        assert preview.site_name == "sub.example.com"
        # No favicon link -> default /favicon.ico.
        assert preview.favicon_url == "https://sub.example.com/favicon.ico"

    def test_falls_back_to_title_tag_and_meta_description(self) -> None:
        preview = extract_link_preview(
            HTML_TITLE_ONLY,
            base_url="https://example.org/",
            requested_url="https://example.org/",
        )
        assert preview.title == "Just Title"
        assert preview.description == "Plain Desc"
        assert preview.image_url is None
        assert preview.site_name == "example.org"

    def test_drops_non_http_image_scheme(self) -> None:
        # og:image is attacker-controlled; a javascript:/data: URI must not
        # survive into image_url (where it would become an <img src>).
        html = (
            "<html><head><title>T</title>"
            "<meta property='og:image' content='javascript:alert(1)'>"
            "</head><body></body></html>"
        )
        preview = extract_link_preview(
            html,
            base_url="https://example.com/",
            requested_url="https://example.com/",
        )
        assert preview.image_url is None
        assert preview.favicon_url == "https://example.com/favicon.ico"


class TestAssertUrlIsSafe:
    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/file",
            "mailto:someone@example.com",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "https:///no-host",
            "http://127.0.0.1/",
            "http://localhost/admin",
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            # IANA shared address space / CGNAT (100.64.0.0/10): not
            # is_private, so a flag denylist would let it through.
            "http://100.64.0.1/",
            # IPv4-mapped IPv6 form of the same CGNAT address.
            "http://[::ffff:100.64.0.1]/",
        ],
    )
    def test_rejects_unsafe_urls(self, url: str) -> None:
        with pytest.raises(UnsafeURLError):
            assert_url_is_safe(url)

    def test_allows_public_ip(self) -> None:
        # 8.8.8.8 resolves to itself offline and is a public address.
        assert_url_is_safe("http://8.8.8.8/")


class TestUnfurlUrl:
    def test_parses_fetched_document(self) -> None:
        fetch = AsyncMock(
            return_value=("https://example.com/p", HTML_FULL.encode())
        )
        with patch("ring.link_unfurl.service._fetch_document", fetch):
            preview = asyncio.run(unfurl_url("https://example.com/p"))
        assert preview.title == "OG Title"
        assert preview.resolved_url == "https://example.com/p"
        fetch.assert_awaited_once()

    def test_caches_repeated_requests(self) -> None:
        fetch = AsyncMock(
            return_value=("https://example.com/c", HTML_FULL.encode())
        )
        with patch("ring.link_unfurl.service._fetch_document", fetch):
            first = asyncio.run(unfurl_url("https://example.com/c"))
            second = asyncio.run(unfurl_url("https://example.com/c"))
        assert first == second
        # The second call is served from the cache.
        fetch.assert_awaited_once()

    def test_empty_url_is_unsafe(self) -> None:
        with pytest.raises(UnsafeURLError):
            asyncio.run(unfurl_url("   "))

    def test_propagates_fetch_errors(self) -> None:
        fetch = AsyncMock(side_effect=LinkUnfurlError("boom"))
        with patch("ring.link_unfurl.service._fetch_document", fetch):
            with pytest.raises(LinkUnfurlError):
                asyncio.run(unfurl_url("https://example.com/err"))


class TestFetchRedirects:
    def test_rejects_redirect_to_non_public_host(self) -> None:
        # A public first hop redirecting to a loopback address must be
        # rejected: redirect re-validation is the key SSRF control.
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                302, headers={"location": "http://127.0.0.1/"}
            )

        with patch(
            "ring.link_unfurl.service.httpx.AsyncClient",
            _mock_async_client(handler),
        ):
            with pytest.raises(UnsafeURLError):
                asyncio.run(unfurl_url("http://8.8.8.8/"))

    def test_follows_redirect_to_public_host(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "8.8.8.8":
                return httpx.Response(
                    307, headers={"location": "http://1.1.1.1/page"}
                )
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text=HTML_FULL,
            )

        with patch(
            "ring.link_unfurl.service.httpx.AsyncClient",
            _mock_async_client(handler),
        ):
            preview = asyncio.run(unfurl_url("http://8.8.8.8/"))
        assert preview.title == "OG Title"
        assert "1.1.1.1" in preview.resolved_url
