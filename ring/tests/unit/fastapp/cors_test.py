"""Tests for CORS middleware configuration in the app factory.

Preflight OPTIONS requests are answered by Starlette's CORSMiddleware before
routing, so these tests never touch the database or run the app lifespan.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from ring.fastapp.config import RingConfig
from ring.fastapp.fast import create_app

PREVIEW_ORIGIN_REGEX = r"^https://[a-z0-9-]+\.ring-cvq\.pages\.dev$"


def _build_config(**overrides: str) -> RingConfig:
    settings: dict[str, str] = {
        "environment": "test",
        "sqlalchemy_database_uri": "postgresql://unused:unused@db/unused",
        "cockroach_database_uri": "cockroachdb://unused:unused@db/unused",
        "JWT_SIGNING_KEY": "test-signing-key",
        "JWT_SIGNING_ALGORITHM": "HS256",
        "VAPID_PRIVATE_KEY": "test-vapid-key",
        "BACKEND_CORS_ORIGINS": "https://ring.neilsriv.tech",
        **overrides,
    }
    return RingConfig(**settings)


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/parties/me",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )


def test_explicit_origin_allowed() -> None:
    config = _build_config()
    with patch("ring.fastapp.fast.get_config", return_value=config):
        client = TestClient(create_app())
    response = _preflight(client, "https://ring.neilsriv.tech")
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://ring.neilsriv.tech"
    )


def test_origin_regex_allows_preview_origins() -> None:
    config = _build_config(BACKEND_CORS_ORIGIN_REGEX=PREVIEW_ORIGIN_REGEX)
    with patch("ring.fastapp.fast.get_config", return_value=config):
        client = TestClient(create_app())
    response = _preflight(client, "https://pr-42.ring-cvq.pages.dev")
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://pr-42.ring-cvq.pages.dev"
    )


def test_origin_regex_rejects_unrelated_origins() -> None:
    config = _build_config(BACKEND_CORS_ORIGIN_REGEX=PREVIEW_ORIGIN_REGEX)
    with patch("ring.fastapp.fast.get_config", return_value=config):
        client = TestClient(create_app())
    response = _preflight(client, "https://evil.example.com")
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_regex_only_config_enables_cors() -> None:
    config = _build_config(
        BACKEND_CORS_ORIGINS="",
        BACKEND_CORS_ORIGIN_REGEX=PREVIEW_ORIGIN_REGEX,
    )
    with patch("ring.fastapp.fast.get_config", return_value=config):
        client = TestClient(create_app())
    response = _preflight(client, "https://pr-7.ring-cvq.pages.dev")
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://pr-7.ring-cvq.pages.dev"
    )
