"""Blindfold push heartbeat for the Ring API.

``@neilsriv/uptime`` is TypeScript-only and is not on npm, and the
Python sender is not published yet. This module is that sender.

POST ``HEARTBEAT_URL`` with HMAC-SHA256 over
``timestamp + "\\n" + body`` (lowercase hex). Headers are
``X-Heartbeat-Key-Id``, ``X-Heartbeat-Timestamp``, and
``X-Heartbeat-Signature``. The body ``serviceId`` is ``ring-api``,
which is also the provisioned key id.

No network call unless ``HEARTBEAT_URL``, ``HEARTBEAT_KEY_ID``, and
``HEARTBEAT_SECRET`` are all non-empty. A shutdown beat uses status
``stopping``.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
import urllib.request
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from loguru import logger

SERVICE_ID = "ring-api"
INTERVAL_SECONDS = 60
_POST_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class HeartbeatConfig:
    url: str
    key_id: str
    secret: str
    service_id: str = SERVICE_ID
    interval_seconds: int = INTERVAL_SECONDS


def config_from_env(
    environ: Mapping[str, str] | None = None,
) -> HeartbeatConfig | None:
    """Return config, or None when any of the three vars is missing."""
    env = os.environ if environ is None else environ
    url = env.get("HEARTBEAT_URL", "").strip()
    key_id = env.get("HEARTBEAT_KEY_ID", "").strip()
    secret = env.get("HEARTBEAT_SECRET", "").strip()
    if not url or not key_id or not secret:
        return None
    return HeartbeatConfig(url=url, key_id=key_id, secret=secret)


def encode_payload(
    *,
    service_id: str,
    status: str,
    version: str,
    interval_seconds: int = INTERVAL_SECONDS,
) -> bytes:
    """JSON body. Key order is sorted so the signature is stable."""
    payload: dict[str, Any] = {
        "instance": service_id,
        "intervalSeconds": interval_seconds,
        "kind": "heartbeat",
        "serviceId": service_id,
        "status": status,
        "version": version,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()


def sign_body(secret: str, timestamp: str, body: bytes) -> str:
    """HMAC-SHA256 hex over ``timestamp + newline + body``."""
    message = timestamp.encode() + b"\n" + body
    return hmac.new(
        secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def signed_headers(
    cfg: HeartbeatConfig, timestamp: str, body: bytes
) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Heartbeat-Key-Id": cfg.key_id,
        "X-Heartbeat-Signature": sign_body(cfg.secret, timestamp, body),
        "X-Heartbeat-Timestamp": timestamp,
    }


def beat_version(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    return (
        env.get("RING_GIT_SHA") or env.get("RING_BUILD_GIT_SHA") or ""
    ).strip()


def _post(cfg: HeartbeatConfig, status: str) -> None:
    body = encode_payload(
        service_id=cfg.service_id,
        status=status,
        version=beat_version(),
        interval_seconds=cfg.interval_seconds,
    )
    timestamp = str(int(time.time()))
    request = urllib.request.Request(
        cfg.url,
        data=body,
        headers=signed_headers(cfg, timestamp, body),
        method="POST",
    )
    with urllib.request.urlopen(
        request, timeout=_POST_TIMEOUT_SECONDS
    ) as response:
        response.read()


async def _loop(cfg: HeartbeatConfig) -> None:
    while True:
        try:
            await asyncio.to_thread(_post, cfg, "ok")
        except Exception:
            logger.warning("Blindfold heartbeat failed")
        await asyncio.sleep(cfg.interval_seconds)


def start_if_configured() -> Callable[[], Awaitable[None]]:
    """Start the beat loop, or return a no-op shutdown.

    Call from a running event loop (the FastAPI lifespan). The returned
    coroutine sends status ``stopping`` when a loop was started.
    """
    cfg = config_from_env()
    if cfg is None:

        async def stop_unconfigured() -> None:
            return

        return stop_unconfigured

    task = asyncio.create_task(_loop(cfg), name="blindfold-heartbeat")

    async def stop() -> None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.warning("Blindfold heartbeat loop stopped")
        try:
            await asyncio.to_thread(_post, cfg, "stopping")
        except Exception:
            logger.warning("Blindfold stopping heartbeat failed")

    return stop
