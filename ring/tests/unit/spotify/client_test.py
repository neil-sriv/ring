"""Spotify Web API batching."""

from __future__ import annotations

import httpx
import pytest

from ring.spotify.client import (
    replace_playlist_tracks,
    save_tracks_to_library,
)
from ring.spotify.settings import SpotifyAppConfig


def _patch_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: httpx.MockTransport,
) -> None:
    real_client = httpx.Client

    def factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs["transport"] = handler
        return real_client(*args, **kwargs)

    monkeypatch.setattr("ring.spotify.client.httpx.Client", factory)


def test_library_save_batches_forty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        uris = request.url.params["uris"].split(",")
        calls.append(len(uris))
        return httpx.Response(200, json={})

    _patch_client(monkeypatch, httpx.MockTransport(handler))
    save_tracks_to_library("token", ["a" * 22] * 41)
    assert calls == [40, 1]


def test_playlist_replace_batches_one_hundred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        calls.append((request.method, len(body["uris"])))
        return httpx.Response(200, json={"snapshot_id": "s"})

    _patch_client(monkeypatch, httpx.MockTransport(handler))
    replace_playlist_tracks("token", "pl", ["b" * 22] * 101)
    assert calls == [("PUT", 100), ("POST", 1)]


def test_app_config_requires_all_three() -> None:
    assert SpotifyAppConfig("", "", "").configured is False
    assert SpotifyAppConfig("id", "secret", "").configured is False
    assert (
        SpotifyAppConfig("id", "secret", "https://example/callback").configured
        is True
    )
