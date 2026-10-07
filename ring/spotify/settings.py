"""Spotify app credentials from the process environment."""

from __future__ import annotations

from dataclasses import dataclass

from ring.fastapp.config import get_config
from ring.spotify.errors import SpotifyNotConfiguredError


@dataclass(frozen=True)
class SpotifyAppConfig:
    """Client id, secret, and redirect URI for the authorization-code flow."""

    client_id: str
    client_secret: str
    redirect_uri: str

    @property
    def configured(self) -> bool:
        """True when every credential needed to link an account is set."""
        return bool(
            self.client_id and self.client_secret and self.redirect_uri
        )


def get_spotify_app_config() -> SpotifyAppConfig:
    """Read Spotify settings from Ring config. Missing values stay blank."""
    config = get_config()
    return SpotifyAppConfig(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
    )


def require_spotify_app_config() -> SpotifyAppConfig:
    """Return Spotify settings or raise when linking is not configured."""
    app_config = get_spotify_app_config()
    if not app_config.configured:
        raise SpotifyNotConfiguredError()
    return app_config
