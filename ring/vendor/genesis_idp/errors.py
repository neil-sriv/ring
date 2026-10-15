"""Errors raised by the identity-service HTTP client."""

from __future__ import annotations


class IdentityClientError(Exception):
    """Identity-service HTTP call failed (non-2xx, timeout, or transport)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        path: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.path = path
        self.error = error
        self.error_description = error_description
