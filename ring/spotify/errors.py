"""Errors raised by Spotify linking."""

from __future__ import annotations


class SpotifyNotConfiguredError(Exception):
    """The server has no Spotify client id, secret, and redirect URI."""


class SpotifyNotLinkedError(Exception):
    """The user has not linked Spotify, or the refresh token was rejected."""


class SpotifyTokenRejectedError(Exception):
    """Spotify refused the refresh token (invalid_grant)."""


class SpotifyPlaylistMissingError(Exception):
    """The stored playlist id no longer exists in the user's account."""


class SpotifyApiError(Exception):
    """Spotify returned an error we cannot complete the action from."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
