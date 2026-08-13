"""Tests for request URL sanitization used by HTTP request logging."""

from __future__ import annotations

import logging

import pytest

from ring.lib.request_logging import (
    UvicornAccessLogRedactionFilter,
    install_uvicorn_access_log_redaction,
    sanitize_request_url,
)


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
            # Uvicorn access logs percent-encode path characters.
            "/api/v1/login/reset-password%3Arequest/leaky%40example.com",
            "/api/v1/login/reset-password:request/[REDACTED]",
        ),
        (
            "/api/v1/invites/token/super-secret-invite-token-xyz",
            "/api/v1/invites/token/[REDACTED]",
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


def test_uvicorn_access_filter_redacts_path_arg() -> None:
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=(
            "127.0.0.1:1234",
            "GET",
            "/api/v1/invites/token/super-secret-invite",
            "1.1",
            400,
        ),
        exc_info=None,
    )
    assert UvicornAccessLogRedactionFilter().filter(record) is True
    assert record.args == (
        "127.0.0.1:1234",
        "GET",
        "/api/v1/invites/token/[REDACTED]",
        "1.1",
        400,
    )


def test_uvicorn_access_filter_redacts_websocket_path() -> None:
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "WebSocket %s" [accepted]',
        args=(
            "127.0.0.1:1234",
            "/api/v1/notebook/ws?token=jwt.secret.value",
        ),
        exc_info=None,
    )
    assert UvicornAccessLogRedactionFilter().filter(record) is True
    assert record.args == (
        "127.0.0.1:1234",
        "/api/v1/notebook/ws?token=%5BREDACTED%5D",
    )


def test_install_uvicorn_access_log_redaction_is_idempotent() -> None:
    access_logger = logging.getLogger("uvicorn.access")
    # Clear filters left by app import or earlier tests so the count is stable.
    access_logger.filters = [
        existing
        for existing in access_logger.filters
        if not isinstance(existing, UvicornAccessLogRedactionFilter)
    ]
    install_uvicorn_access_log_redaction()
    install_uvicorn_access_log_redaction()
    assert (
        sum(
            isinstance(existing, UvicornAccessLogRedactionFilter)
            for existing in access_logger.filters
        )
        == 1
    )
