"""Tests for GET /version."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from ring.fastapp.api import version as version_api
from ring.fastapp.schemas.version import (
    DockerInfo,
    GitCommitInfo,
    VersionResponse,
)


@pytest.fixture
def stubbed_version() -> Generator[VersionResponse, None, None]:
    payload = VersionResponse(
        hostname="ring-api",
        git=GitCommitInfo(
            sha="checkoutsha",
            short_sha="checkou",
            branch="dev",
            subject="live checkout",
            source="git",
        ),
        image_build=GitCommitInfo(
            sha="imagesha",
            short_sha="imagesh",
            subject="baked",
            source="image_env",
        ),
        docker=DockerInfo(
            available=True,
            socket_path="/var/run/docker.sock",
            project="ring",
            containers=[],
        ),
    )

    def fake_get_version(**kwargs: Any) -> VersionResponse:
        return payload

    with patch.object(version_api, "get_version", fake_get_version):
        yield payload


class TestVersionAPI:
    def test_version_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        stubbed_version: VersionResponse,
    ) -> None:
        response = unauthenticated_client.get("/version")
        assert response.status_code == 200
        body = response.json()
        assert body["hostname"] == "ring-api"
        assert body["git"]["sha"] == "checkoutsha"
        assert body["git"]["source"] == "git"
        assert body["image_build"]["sha"] == "imagesha"
        assert body["docker"]["available"] is True
        assert body["docker"]["containers"] == []

    def test_version_returns_live_collection(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.get("/version")
        assert response.status_code == 200
        body = response.json()
        assert "git" in body
        assert "image_build" in body
        assert "docker" in body
        assert body["git"]["source"] in {
            "git",
            "env",
            "image_env",
            "unavailable",
        }
        assert isinstance(body["docker"]["containers"], list)
        assert isinstance(body["hostname"], str)
        serialized = str(body)
        assert "JWT_SIGNING_KEY" not in serialized
        assert "VAPID_PRIVATE_KEY" not in serialized
