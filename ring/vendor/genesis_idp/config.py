"""Constructor config for the HTTP identity-service client.

Kept free of Ring's ``RingConfig`` so this package can be extracted later.
Base URL, bearer token, and path templates live here so a locked IdP
contract is a config change.
"""

from __future__ import annotations

from dataclasses import dataclass

from .paths import (
    DEFAULT_COLLECTION_PATH,
    DEFAULT_IDENTITY_PATH,
)


@dataclass(frozen=True)
class IdentityClientConfig:
    """IdP origin, static bearer token, paths, timeout, and 502 retries."""

    base_url: str
    api_token: str
    timeout_seconds: float = 2.0
    identity_path: str = DEFAULT_IDENTITY_PATH
    collection_path: str = DEFAULT_COLLECTION_PATH
    write_retries: int = 3

    @property
    def configured(self) -> bool:
        """True when origin and bearer token are both set."""
        return bool(self.base_url and self.api_token)
