"""Helpers for safe HTTP request logging.

The FastAPI request logger records method + URL. Some routes put one-time tokens
or emails in the path (invite validation, registration, password reset), and
WebSocket auth puts JWTs in query params. This module redacts those values so
they do not end up in console/file logs.

Uvicorn's separate ``uvicorn.access`` logger also records request targets (often
URL-encoded). Install :func:`install_uvicorn_access_log_redaction` so those
lines are redacted with the same rules.
"""

from __future__ import annotations

import logging
import re
from typing import Final
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

# Path prefixes where the next segment is a secret (token) or email.
_SENSITIVE_PATH_PREFIXES: Final[tuple[str, ...]] = (
    "/token/",
    "/register/",
    "/reset-password/",
    "/reset-password:request/",
)

_SENSITIVE_QUERY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "password",
        "authorization",
    }
)

_REDACTED: Final[str] = "[REDACTED]"


def sanitize_request_url(url: str) -> str:
    """Return a log-safe copy of ``url`` with secrets replaced by ``[REDACTED]``.

    Redacts:
    - Path segments immediately after known sensitive prefixes
    - Query parameter values whose keys are sensitive (case-insensitive)

    Path percent-encoding is decoded before matching prefixes so uvicorn access
    lines like ``/reset-password%3Arequest/user%40x.com`` are covered.

    Args:
        url: Full request URL or request target (path + optional query).

    Returns:
        The same URL with sensitive path/query values redacted.
    """
    parts = urlsplit(url)
    path = _redact_path(unquote(parts.path))
    query = _redact_query(parts.query)
    return urlunsplit(
        (parts.scheme, parts.netloc, path, query, parts.fragment)
    )


def _redact_path(path: str) -> str:
    redacted = path
    for prefix in _SENSITIVE_PATH_PREFIXES:
        # Match prefix + non-empty segment (stop at next slash or end).
        pattern = re.compile(
            re.escape(prefix) + r"[^/]+",
            flags=re.IGNORECASE,
        )
        redacted = pattern.sub(f"{prefix}{_REDACTED}", redacted)
    return redacted


def _redact_query(query: str) -> str:
    if not query:
        return query
    pairs = parse_qsl(query, keep_blank_values=True)
    redacted_pairs: list[tuple[str, str]] = []
    for key, value in pairs:
        if key.lower() in _SENSITIVE_QUERY_KEYS:
            redacted_pairs.append((key, _REDACTED))
        else:
            redacted_pairs.append((key, value))
    return urlencode(redacted_pairs)


def _looks_like_request_target(value: str) -> bool:
    """True when ``value`` is a URL or HTTP request target worth sanitizing."""
    return value.startswith("/") or "://" in value


class UvicornAccessLogRedactionFilter(logging.Filter):
    """Redact secrets in ``uvicorn.access`` log record args before emit."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and args:
            record.args = tuple(
                sanitize_request_url(arg)
                if isinstance(arg, str) and _looks_like_request_target(arg)
                else arg
                for arg in args
            )
        elif isinstance(args, dict):
            record.args = {
                key: (
                    sanitize_request_url(value)
                    if isinstance(value, str)
                    and _looks_like_request_target(value)
                    else value
                )
                for key, value in args.items()
            }
        return True


def install_uvicorn_access_log_redaction() -> None:
    """Attach :class:`UvicornAccessLogRedactionFilter` to ``uvicorn.access``.

    Safe to call multiple times (idempotent). Should run when the API process
    starts so access lines never leak invite/reset tokens or emails.
    """
    access_logger = logging.getLogger("uvicorn.access")
    if any(
        isinstance(existing, UvicornAccessLogRedactionFilter)
        for existing in access_logger.filters
    ):
        return
    access_logger.addFilter(UvicornAccessLogRedactionFilter())
