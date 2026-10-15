"""Thin Ring wiring over the genesis-idp SDK.

Sync ``HttpIdentityClient`` only (not ``genesis_idp.aio``). Dual-sync runs in
FastAPI BackgroundTasks and CLI scripts.
"""

from __future__ import annotations

from genesis_idp import (
    HttpIdentityClient,
    IdentityClient,
    IdentityClientConfig,
)

from ring.fastapp.config import RingConfig, get_config

_override: IdentityClient | None = None
_http_client: HttpIdentityClient | None = None


def identity_client_config_from_ring(
    config: RingConfig | None = None,
) -> IdentityClientConfig:
    """Map Ring settings onto genesis-idp ``IdentityClientConfig``."""
    ring_config = config or get_config()
    return IdentityClientConfig(
        base_url=ring_config.IDENTITY_SERVICE_BASE_URL,
        api_token=ring_config.IDP_DIRECTORY_API_TOKEN,
        timeout_seconds=ring_config.AUTH_DUAL_SYNC_TIMEOUT_SECONDS,
        identity_path=ring_config.IDENTITY_SERVICE_IDENTITY_PATH,
        collection_path=ring_config.IDENTITY_SERVICE_COLLECTION_PATH,
    )


def set_identity_client_override(
    client: IdentityClient | None,
) -> None:
    """Tests inject a fake; pass None to restore HTTP construction."""
    global _override
    _override = client


def get_identity_client() -> IdentityClient | None:
    """Return override, a cached HTTP client, or None if unconfigured."""
    if _override is not None:
        return _override
    config = identity_client_config_from_ring()
    if not config.configured:
        return None
    global _http_client
    if _http_client is None:
        _http_client = HttpIdentityClient(config)
    return _http_client


def reset_identity_client_cache() -> None:
    """Drop the cached HTTP client (tests)."""
    global _http_client
    if _http_client is not None:
        _http_client.close()
    _http_client = None
