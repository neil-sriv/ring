"""Blindfold push heartbeat for the Ring API.

``@neilsriv/uptime`` is not on npm, and there is no Python package yet,
so this module is the sender. The schedule lives in
``ring.fastapp.blindfold_job``: an APScheduler interval job in this
API process, not a separate worker.

POST ``HEARTBEAT_URL`` with HMAC-SHA256 over
``timestamp + "\\n" + body`` (lowercase hex). Headers are
``X-Heartbeat-Key-Id``, ``X-Heartbeat-Timestamp``, and
``X-Heartbeat-Signature``. ``serviceId`` is ``ring-api``.

No network call unless ``HEARTBEAT_URL``, ``HEARTBEAT_KEY_ID``, and
``HEARTBEAT_SECRET`` are all set. Each beat reports
``intervalSeconds`` 300. Blindfold treats that as stale after about
12.5 minutes. There is no ``stopping`` beat: a deploy finishes well
inside that window, and a crash would not send one anyway.

An ``ok`` beat means the scheduler job ran and ``GET /`` on
``127.0.0.1:$API_PORT`` returned 2xx. It does not prove nginx,
Cloudflare, or the public hostname. If that request never connects,
nothing is posted.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from loguru import logger

SERVICE_ID = "ring-api"
INTERVAL_SECONDS = 300
_TIMEOUT_SECONDS = 5
_UNREACHABLE = "unreachable"


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


def local_health_url(environ: Mapping[str, str] | None = None) -> str:
    """Loopback URL for the API's ``GET /`` health route."""
    env = os.environ if environ is None else environ
    port = env.get("API_PORT", "").strip() or "8001"
    return f"http://127.0.0.1:{port}/"


def probe_local_api(environ: Mapping[str, str] | None = None) -> str:
    """Return ``ok``, ``down``, or ``unreachable``.

    ``GET /`` is the in-process health route. Connection failure is
    ``unreachable`` so a startup race does not post ``down``.
    """
    request = urllib.request.Request(local_health_url(environ), method="GET")
    try:
        with urllib.request.urlopen(
            request, timeout=_TIMEOUT_SECONDS
        ) as response:
            if 200 <= response.status < 300:
                return "ok"
            return "down"
    except urllib.error.HTTPError as exc:
        if 200 <= exc.code < 300:
            return "ok"
        return "down"
    except (urllib.error.URLError, TimeoutError, OSError):
        return _UNREACHABLE


def post_beat(
    cfg: HeartbeatConfig,
    status: str,
    *,
    version: str | None = None,
) -> None:
    body = encode_payload(
        service_id=cfg.service_id,
        status=status,
        version=beat_version() if version is None else version,
        interval_seconds=cfg.interval_seconds,
    )
    timestamp = str(int(time.time()))
    request = urllib.request.Request(
        cfg.url,
        data=body,
        headers=signed_headers(cfg, timestamp, body),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        response.read()


def run_heartbeat(environ: Mapping[str, str] | None = None) -> str | None:
    """Probe local health and post one beat.

    Returns the posted status, or None when unconfigured, when the
    local server did not connect, or when the POST failed.
    """
    cfg = config_from_env(environ)
    if cfg is None:
        return None
    status = probe_local_api(environ)
    if status == _UNREACHABLE:
        logger.warning(
            "Blindfold heartbeat skipped; local API did not respond"
        )
        return None
    try:
        post_beat(cfg, status)
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.warning("Blindfold heartbeat failed")
        return None
    return status
