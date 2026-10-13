"""Spotify OAuth state and authorization URL.

The callback is a browser redirect and may not carry the Ring bearer token,
so the signed state identifies the user and the in-app path to return to.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jose import JWTError, jwt

from ring.fastapp.config import get_config
from ring.spotify.settings import SpotifyAppConfig

STATE_PURPOSE = "spotify_oauth"
STATE_TTL_SECONDS = 10 * 60
SCOPES = (
    "user-library-modify",
    "playlist-modify-private",
)
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"


def safe_return_path(return_to: str) -> str:
    """Keep an in-app path. Anything else becomes the site root."""
    if (
        not return_to.startswith("/")
        or return_to.startswith("//")
        or "\\" in return_to
    ):
        return "/"
    parts = urlsplit(return_to)
    if parts.scheme or parts.netloc:
        return "/"
    return return_to


def create_oauth_state(user_api_id: str, return_to: str) -> str:
    """Sign a short-lived state token for the Spotify authorize redirect."""
    config = get_config()
    payload = {
        "sub": user_api_id,
        "purpose": STATE_PURPOSE,
        "return_to": safe_return_path(return_to),
        "exp": datetime.now(tz=UTC) + timedelta(seconds=STATE_TTL_SECONDS),
    }
    return jwt.encode(
        payload,
        config.JWT_SIGNING_KEY,
        algorithm=config.JWT_SIGNING_ALGORITHM,
    )


def decode_oauth_state(state: str) -> tuple[str, str]:
    """Return ``(user_api_id, return_to)`` or raise ``ValueError``."""
    config = get_config()
    try:
        payload = jwt.decode(
            state,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError("invalid state") from exc
    if payload.get("purpose") != STATE_PURPOSE:
        raise ValueError("invalid state")
    user_api_id = payload.get("sub")
    return_to = payload.get("return_to") or "/"
    if not isinstance(user_api_id, str) or not user_api_id:
        raise ValueError("invalid state")
    if not isinstance(return_to, str):
        return_to = "/"
    return user_api_id, safe_return_path(return_to)


def authorization_url(state: str, app_config: SpotifyAppConfig) -> str:
    """Build the Spotify authorize URL for this app and state token."""
    query = urlencode(
        {
            "response_type": "code",
            "client_id": app_config.client_id,
            "scope": " ".join(SCOPES),
            "redirect_uri": app_config.redirect_uri,
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def redirect_location(return_to: str, **params: str) -> str:
    """Absolute app URL for the browser after the OAuth callback."""
    base = get_config().APP_BASE_URL.rstrip("/")
    safe = safe_return_path(return_to)
    parts = urlsplit(safe)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        if value:
            query[key] = value
    path = urlunsplit(
        ("", "", parts.path or "/", urlencode(query), parts.fragment)
    )
    return f"{base}{path}"


def safe_oauth_error(error: str | None) -> str:
    """Limit Spotify's error query value to a short token."""
    if error and error.isascii() and error.replace("_", "").isalnum():
        if len(error) <= 64:
            return error
    return "denied"
