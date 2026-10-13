"""HTTP calls to Spotify accounts and the Web API."""

from __future__ import annotations

import base64

import httpx

from ring.spotify.errors import (
    SpotifyApiError,
    SpotifyPlaylistMissingError,
    SpotifyTokenRejectedError,
)
from ring.spotify.settings import SpotifyAppConfig, require_spotify_app_config

ACCOUNTS_TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
LIBRARY_BATCH = 40
PLAYLIST_BATCH = 100
_TIMEOUT = 15.0


def _client() -> httpx.Client:
    return httpx.Client(timeout=_TIMEOUT)


def _basic_auth(app_config: SpotifyAppConfig) -> str:
    raw = f"{app_config.client_id}:{app_config.client_secret}".encode()
    token = base64.b64encode(raw).decode("ascii")
    return f"Basic {token}"


def _token_payload(response: httpx.Response) -> dict[str, object]:
    if response.status_code >= 400:
        error = ""
        try:
            body = response.json()
        except ValueError:
            body = {}
        if isinstance(body, dict):
            error = str(body.get("error") or "")
        if error == "invalid_grant":
            raise SpotifyTokenRejectedError()
        raise SpotifyApiError("token_request_failed")
    try:
        body = response.json()
    except ValueError as exc:
        raise SpotifyApiError("token_request_failed") from exc
    if not isinstance(body, dict):
        raise SpotifyApiError("token_request_failed")
    return body


def exchange_authorization_code(code: str) -> str:
    """Trade an authorization code for a refresh token."""
    app_config = require_spotify_app_config()
    with _client() as client:
        response = client.post(
            ACCOUNTS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": app_config.redirect_uri,
            },
            headers={"Authorization": _basic_auth(app_config)},
        )
    body = _token_payload(response)
    refresh_token = body.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise SpotifyApiError("token_request_failed")
    return refresh_token


def refresh_access_token(refresh_token: str) -> tuple[str, str | None]:
    """Return ``(access_token, rotated_refresh_token_or_none)``."""
    app_config = require_spotify_app_config()
    with _client() as client:
        response = client.post(
            ACCOUNTS_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Authorization": _basic_auth(app_config)},
        )
    body = _token_payload(response)
    access_token = body.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise SpotifyApiError("token_request_failed")
    rotated = body.get("refresh_token")
    if isinstance(rotated, str) and rotated and rotated != refresh_token:
        return access_token, rotated
    return access_token, None


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _raise_for_api(response: httpx.Response) -> dict[str, object] | None:
    if response.status_code == 404:
        raise SpotifyPlaylistMissingError()
    if response.status_code >= 400:
        raise SpotifyApiError(f"spotify_http_{response.status_code}")
    if not response.content:
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        return body
    return None


def save_tracks_to_library(access_token: str, track_ids: list[str]) -> None:
    """Save track ids to the current Spotify user's library."""
    if not track_ids:
        return
    with _client() as client:
        for start in range(0, len(track_ids), LIBRARY_BATCH):
            chunk = track_ids[start : start + LIBRARY_BATCH]
            uris = ",".join(f"spotify:track:{track_id}" for track_id in chunk)
            response = client.put(
                f"{API_BASE}/me/library",
                headers=_bearer(access_token),
                params={"uris": uris},
            )
            _raise_for_api(response)


def create_playlist(access_token: str, name: str) -> str:
    """Create a private playlist and return its Spotify id."""
    with _client() as client:
        response = client.post(
            f"{API_BASE}/me/playlists",
            headers=_bearer(access_token),
            json={
                "name": name[:100],
                "public": False,
                "description": _playlist_description(name),
            },
        )
    body = _raise_for_api(response) or {}
    playlist_id = body.get("id")
    if not isinstance(playlist_id, str) or not playlist_id:
        raise SpotifyApiError("playlist_create_failed")
    return playlist_id


def update_playlist_name(
    access_token: str, playlist_id: str, name: str
) -> None:
    """Rename a playlist the user owns."""
    with _client() as client:
        response = client.put(
            f"{API_BASE}/playlists/{playlist_id}",
            headers=_bearer(access_token),
            json={
                "name": name[:100],
                "description": _playlist_description(name),
                "public": False,
            },
        )
    _raise_for_api(response)


def replace_playlist_tracks(
    access_token: str, playlist_id: str, track_ids: list[str]
) -> None:
    """Replace the playlist contents with these tracks, in order."""
    uris = [f"spotify:track:{track_id}" for track_id in track_ids]
    first = uris[:PLAYLIST_BATCH]
    with _client() as client:
        response = client.put(
            f"{API_BASE}/playlists/{playlist_id}/items",
            headers=_bearer(access_token),
            json={"uris": first},
        )
        _raise_for_api(response)
        for start in range(PLAYLIST_BATCH, len(uris), PLAYLIST_BATCH):
            chunk = uris[start : start + PLAYLIST_BATCH]
            response = client.post(
                f"{API_BASE}/playlists/{playlist_id}/items",
                headers=_bearer(access_token),
                json={"uris": chunk},
            )
            _raise_for_api(response)


def _playlist_description(name: str) -> str:
    description = f"Tracks from {name} on Ring"
    return description[:300]


def playlist_url(playlist_id: str) -> str:
    """Public open.spotify.com URL for a playlist id."""
    return f"https://open.spotify.com/playlist/{playlist_id}"
