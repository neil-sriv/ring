"""Tests for the crawler-facing HTML behind link previews."""

from __future__ import annotations

from html import escape

from fastapi.testclient import TestClient

from ring.unfurl.api.unfurl import render_unfurl_html
from ring.unfurl.cards import card_for_path


class TestUnfurlAPI:
    """Test suite for `GET /unfurl/{app_path}`."""

    def test_serves_html_without_authentication(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Crawlers arrive with no session and must still get a card."""
        response = unauthenticated_client.get("/unfurl/loops/lttr_abc123")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert 'property="og:title"' in response.text

    def test_answers_head_probes(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Crawlers that probe with HEAD give up on a 405."""
        response = unauthenticated_client.head("/unfurl/loops/lttr_abc123")

        assert response.status_code == 200

    def test_letter_path_gets_letter_copy(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.get("/unfurl/loops/lttr_abc123")

        assert 'content="A newsletter on Ring"' in response.text

    def test_unknown_path_falls_back_to_the_site_card(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.get("/unfurl/")

        assert response.status_code == 200
        assert 'property="og:title" content="Ring"' in response.text

    def test_response_varies_on_user_agent(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Nginx serves this body only to crawlers, never to browsers."""
        response = unauthenticated_client.get("/unfurl/loops/lttr_abc123")

        assert response.headers["vary"] == "User-Agent"
        assert "max-age" in response.headers["cache-control"]

    def test_copy_is_the_static_card_for_the_path(
        self, unauthenticated_client: TestClient
    ) -> None:
        """A preview renders for a whole channel, so copy names nothing."""
        card = card_for_path("loops")
        response = unauthenticated_client.get("/unfurl/loops/lttr_abc123")

        assert (
            f'property="og:title" content="{escape(card.title)}"'
            in response.text
        )
        assert (
            f'property="og:description" content="{escape(card.description)}"'
            in response.text
        )


class TestRenderUnfurlHtml:
    """Test suite for the rendered document itself."""

    def test_tags_every_chat_client_reads(self) -> None:
        html = render_unfurl_html("/loops/lttr_abc123")

        for tag in (
            'property="og:site_name"',
            'property="og:type"',
            'property="og:title"',
            'property="og:description"',
            'property="og:url"',
            'property="og:image"',
            'name="twitter:card" content="summary_large_image"',
        ):
            assert tag in html

    def test_preview_tags_land_in_slack_range_request(self) -> None:
        """Slack reads only the first 32KB of the response."""
        html = render_unfurl_html("/loops/lttr_abc123")

        assert html.index('property="og:image"') < 32 * 1024

    def test_image_url_is_absolute_and_https(self) -> None:
        """A relative og:image renders as no image at all."""
        html = render_unfurl_html("/loops/lttr_abc123")

        assert 'content="https://' in html
        assert "og-card.png" in html

    def test_canonical_url_points_at_the_shared_path(self) -> None:
        html = render_unfurl_html("/loops/lttr_abc123")

        assert "/loops/lttr_abc123" in html

    def test_path_is_escaped_into_attributes(self) -> None:
        """The path comes off the request line, so it cannot break out."""
        html = render_unfurl_html('/loops/"><script>alert(1)</script>')

        assert "<script>" not in html
        assert "&lt;script&gt;" in html
