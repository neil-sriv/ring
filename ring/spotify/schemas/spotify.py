"""Request and response schemas for Spotify linking."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpotifyStatus(BaseModel):
    """Whether this server can link Spotify and whether the user has."""

    configured: bool
    linked: bool


class SpotifyAuthorizeRequest(BaseModel):
    """Where to send the browser after Spotify redirects back."""

    return_to: str = "/"


class SpotifyAuthorizeResponse(BaseModel):
    """Spotify authorization URL for the browser to open."""

    authorization_url: str


class SpotifyLibrarySaveResponse(BaseModel):
    """Tracks from a letter that were saved to the user's library."""

    saved_count: int
    track_ids: list[str] = Field(default_factory=list)


class SpotifyPlaylistResponse(BaseModel):
    """A playlist in the current user's Spotify account."""

    playlist_id: str
    playlist_url: str
    name: str
    track_count: int
