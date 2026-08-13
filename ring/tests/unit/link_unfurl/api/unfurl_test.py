"""Tests for the link unfurl API endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from ring.link_unfurl.schemas.link_preview import LinkPreview
from ring.link_unfurl.service import LinkUnfurlError, UnsafeURLError

_UNFURL_TARGET = "ring.link_unfurl.api.unfurl.unfurl_url"


class TestUnfurlAPI:
    def test_returns_preview(self, authenticated_client: TestClient) -> None:
        preview = LinkPreview(
            url="https://example.com/p",
            resolved_url="https://example.com/p",
            title="OG Title",
            description="OG Description",
            image_url="https://example.com/img.png",
            site_name="Example Site",
            favicon_url="https://example.com/favicon.ico",
        )
        with patch(_UNFURL_TARGET, AsyncMock(return_value=preview)):
            response = authenticated_client.post(
                "/links/unfurl", json={"url": "https://example.com/p"}
            )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "OG Title"
        assert body["site_name"] == "Example Site"
        assert body["image_url"] == "https://example.com/img.png"

    def test_unsafe_url_returns_400(
        self, authenticated_client: TestClient
    ) -> None:
        with patch(
            _UNFURL_TARGET,
            AsyncMock(side_effect=UnsafeURLError("nope")),
        ):
            response = authenticated_client.post(
                "/links/unfurl", json={"url": "http://127.0.0.1/"}
            )
        assert response.status_code == 400

    def test_fetch_failure_returns_502(
        self, authenticated_client: TestClient
    ) -> None:
        with patch(
            _UNFURL_TARGET,
            AsyncMock(side_effect=LinkUnfurlError("boom")),
        ):
            response = authenticated_client.post(
                "/links/unfurl", json={"url": "https://example.com/x"}
            )
        assert response.status_code == 502

    def test_unsafe_url_through_real_service(
        self, authenticated_client: TestClient
    ) -> None:
        # No mocking: loopback addresses are rejected before any network
        # call, so this exercises the real SSRF guard offline.
        response = authenticated_client.post(
            "/links/unfurl", json={"url": "http://127.0.0.1/"}
        )
        assert response.status_code == 400

    def test_requires_authentication(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.post(
            "/links/unfurl", json={"url": "https://example.com/p"}
        )
        assert response.status_code == 401
