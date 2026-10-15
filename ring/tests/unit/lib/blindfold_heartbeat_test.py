"""Tests for the Blindfold heartbeat signer."""

from __future__ import annotations

import inspect
import io
import urllib.error
from pathlib import Path

import pytest
from loguru import logger

from ring.lib.blindfold_heartbeat import (
    INTERVAL_SECONDS,
    USER_AGENT,
    HeartbeatConfig,
    config_from_env,
    encode_payload,
    local_health_url,
    run_heartbeat,
    sign_body,
    signed_headers,
)

VECTOR_BODY = (
    b'{"instance":"ring-api","intervalSeconds":300,'
    b'"kind":"heartbeat","serviceId":"ring-api",'
    b'"status":"ok","version":"abc"}'
)
VECTOR_SIG = "90f343d950cb9ae2573067b446ca0bd7d59c668f54588c3f5fd7078584220ceb"

_ENV = {
    "HEARTBEAT_URL": "https://example.test/api/heartbeat",
    "HEARTBEAT_KEY_ID": "ring-api",
    "HEARTBEAT_SECRET": "test-secret",
    "API_PORT": "8001",
    "RING_GIT_SHA": "abc",
}


class _Response:
    def __init__(self, status: int, body: bytes = b"") -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


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
    assert INTERVAL_SECONDS == 300
    assert sign_body("test-secret", "1700000000", body) == VECTOR_SIG


def test_headers_carry_the_signature_and_not_the_secret() -> None:
    cfg = HeartbeatConfig(
        url="https://example.test/api/heartbeat",
        key_id="ring-api",
        secret="test-secret",
    )
    headers = signed_headers(cfg, "1700000000", VECTOR_BODY)
    assert headers["User-Agent"] == USER_AGENT
    assert "Python-urllib" not in headers["User-Agent"]
    assert headers["X-Heartbeat-Key-Id"] == "ring-api"
    assert headers["X-Heartbeat-Timestamp"] == "1700000000"
    assert headers["X-Heartbeat-Signature"] == VECTOR_SIG
    assert "test-secret" not in headers.values()
    assert b"test-secret" not in VECTOR_BODY


def test_unconfigured_run_does_not_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("posted")

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        explode,
    )
    assert run_heartbeat({}) is None


def test_ok_beat_follows_a_local_health_200(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def urlopen(
        request: urllib.request.Request, timeout: float = 0
    ) -> _Response:
        seen.append(request.full_url)
        if request.full_url == local_health_url(_ENV):
            return _Response(200, b'{"message":"Hello World!"}')
        body = request.data or b""
        assert b'"intervalSeconds":300' in body
        assert b'"status":"ok"' in body
        assert b"test-secret" not in body
        return _Response(204)

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        urlopen,
    )
    assert run_heartbeat(_ENV) == "ok"
    assert seen == [
        "http://127.0.0.1:8001/",
        "https://example.test/api/heartbeat",
    ]


def test_http_error_posts_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen(
        request: urllib.request.Request, timeout: float = 0
    ) -> _Response:
        if request.full_url.startswith("http://127.0.0.1"):
            raise urllib.error.HTTPError(
                request.full_url, 500, "down", None, None
            )
        assert b'"status":"down"' in (request.data or b"")
        return _Response(204)

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        urlopen,
    )
    assert run_heartbeat(_ENV) == "down"


def _capture_logs() -> tuple[list[str], int]:
    captured: list[str] = []
    handler_id = logger.add(lambda message: captured.append(str(message)))
    return captured, handler_id


def test_post_http_error_logs_status_and_short_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prefix = b"error code: 1010"
    body = prefix + (b"x" * (200 - len(prefix))) + b"TAIL_MARKER"
    seen_agent: list[str | None] = []

    def urlopen(
        request: urllib.request.Request, timeout: float = 0
    ) -> _Response:
        if request.full_url.startswith("http://127.0.0.1"):
            return _Response(200, b'{"message":"Hello World!"}')
        seen_agent.append(request.get_header("User-agent"))
        raise urllib.error.HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs=None,
            fp=io.BytesIO(body),
        )

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.time.time",
        lambda: 1700000000,
    )
    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        urlopen,
    )
    captured, handler_id = _capture_logs()
    try:
        assert run_heartbeat(_ENV) is None
    finally:
        logger.remove(handler_id)

    text = "\n".join(captured)
    assert seen_agent == [USER_AGENT]
    assert "HTTP 403" in text
    assert body[:200].decode() in text
    assert "TAIL_MARKER" not in text
    assert "test-secret" not in text
    assert VECTOR_SIG not in text


def test_post_url_error_logs_exception_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen(
        request: urllib.request.Request, timeout: float = 0
    ) -> _Response:
        if request.full_url.startswith("http://127.0.0.1"):
            return _Response(200, b"ok")
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        urlopen,
    )
    captured, handler_id = _capture_logs()
    try:
        assert run_heartbeat(_ENV) is None
    finally:
        logger.remove(handler_id)

    text = "\n".join(captured)
    assert "URLError" in text
    assert "connection refused" in text
    assert "test-secret" not in text


def test_unreachable_api_does_not_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen(
        request: urllib.request.Request, timeout: float = 0
    ) -> _Response:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(
        "ring.lib.blindfold_heartbeat.urllib.request.urlopen",
        urlopen,
    )
    assert run_heartbeat(_ENV) is None


def test_job_is_wired_to_the_scheduler_import() -> None:
    from ring.fastapp._gen import all_jobs

    source = inspect.getsource(all_jobs.import_all_jobs)
    assert "ring.fastapp.blindfold_job" in source
    import ring.fastapp

    job = Path(ring.fastapp.__file__).resolve().parent / "blindfold_job.py"
    text = job.read_text()
    assert "minutes=INTERVAL_SECONDS // 60" in text
    assert "run_heartbeat" in text
