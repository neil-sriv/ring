"""Helpers for safe HTTP request logging.

The FastAPI request logger records method + URL. Some routes put one-time tokens
or emails in the path (invite validation, registration, password reset), and
WebSocket auth puts JWTs in query params. This module redacts those values so
they do not end up in console/file logs.
"""

from __future__ import annotations

import re
from typing import Final
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

    Args:
        url: Full request URL (as logged by Starlette ``request.url``).

    Returns:
        The same URL with sensitive path/query values redacted.
    """
    parts = urlsplit(url)
    path = _redact_path(parts.path)
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
