"""Tests for the Blindfold heartbeat signer."""

from __future__ import annotations

import asyncio

import pytest

from ring.lib.blindfold_heartbeat import (
    HeartbeatConfig,
    config_from_env,
    encode_payload,
    sign_body,
    signed_headers,
    start_if_configured,
)

VECTOR_BODY = (
    b'{"instance":"ring-api","intervalSeconds":300,'
    b'"kind":"heartbeat","serviceId":"ring-api",'
    b'"status":"ok","version":"abc"}'
)
VECTOR_SIG = "90f343d950cb9ae2573067b446ca0bd7d59c668f54588c3f5fd7078584220ceb"


def test_missing_or_blank_env_is_unconfigured() -> None:
    assert config_from_env({}) is None
    assert (
        config_from_env(
            {
                "HEARTBEAT_URL": "https://example.test/api/heartbeat",
                "HEARTBEAT_KEY_ID": "ring-api",
            }
        )
        is None
    )
    assert (
        config_from_env(
            {
                "HEARTBEAT_URL": "  ",
                "HEARTBEAT_KEY_ID": "ring-api",
                "HEARTBEAT_SECRET": "test-secret",
            }
        )
        is None
    )


def test_encode_and_sign_match_the_documented_construction() -> None:
    body = encode_payload(
        service_id="ring-api",
        status="ok",
        version="abc",
    )
    assert body == VECTOR_BODY
    assert sign_body("test-secret", "1700000000", body) == VECTOR_SIG


def test_headers_carry_the_signature_and_not_the_secret() -> None:
    cfg = HeartbeatConfig(
        url="https://example.test/api/heartbeat",
        key_id="ring-api",
        secret="test-secret",
    )
    headers = signed_headers(cfg, "1700000000", VECTOR_BODY)
    assert headers["X-Heartbeat-Key-Id"] == "ring-api"
    assert headers["X-Heartbeat-Timestamp"] == "1700000000"
    assert headers["X-Heartbeat-Signature"] == VECTOR_SIG
    assert "test-secret" not in headers.values()
    assert b"test-secret" not in VECTOR_BODY


def test_unconfigured_start_does_not_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEARTBEAT_URL", raising=False)
    monkeypatch.delenv("HEARTBEAT_KEY_ID", raising=False)
    monkeypatch.delenv("HEARTBEAT_SECRET", raising=False)

    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("posted")

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        explode,
    )
    stop = start_if_configured()
    asyncio.run(stop())
