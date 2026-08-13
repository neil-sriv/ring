"""Tests for the link unfurling service.

Covers HTML metadata extraction, SSRF safety checks, and the caching
behaviour of ``unfurl_url``. Async code is driven via ``asyncio.run`` since
the project does not use an asyncio pytest plugin.
"""

from __future__ import annotations

import asyncio
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest

from ring.link_unfurl.service import (
    LinkUnfurlError,
    UnsafeURLError,
    assert_url_is_safe,
    clear_link_preview_cache,
    extract_link_preview,
    unfurl_url,
)

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
