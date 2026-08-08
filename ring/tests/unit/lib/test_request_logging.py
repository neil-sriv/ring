"""Tests for request URL sanitization used by HTTP request logging."""

from __future__ import annotations

import pytest

from ring.lib.request_logging import sanitize_request_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "http://test/api/v1/invites/token/super-secret-invite",
            "http://test/api/v1/invites/token/[REDACTED]",
        ),
        (
            "http://test/api/v1/parties/register/abc123token",
            "http://test/api/v1/parties/register/[REDACTED]",
        ),
        (
            "http://test/api/v1/login/reset-password/reset-secret",
            "http://test/api/v1/login/reset-password/[REDACTED]",
        ),
        (
            "http://test/api/v1/login/reset-password:request/user@example.com",
            "http://test/api/v1/login/reset-password:request/[REDACTED]",
        ),
        (
            "http://test/api/v1/notebook/ws?token=jwt.secret.value&doc=1",
            "http://test/api/v1/notebook/ws?token=%5BREDACTED%5D&doc=1",
        ),
        (
            "http://test/api/v1/parties/me",
            "http://test/api/v1/parties/me",
        ),
        (
            "http://test/api/v1/search/?q=hello&access_token=leak",
            "http://test/api/v1/search/?q=hello&access_token=%5BREDACTED%5D",
        ),
    ],
)
def test_sanitize_request_url_redacts_secrets(raw: str, expected: str) -> None:
    assert sanitize_request_url(raw) == expected


def test_sanitize_request_url_does_not_mutate_unrelated_segments() -> None:
    url = "http://test/api/v1/groups/grp_123/members"
    assert sanitize_request_url(url) == url
