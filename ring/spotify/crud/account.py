"""Stored Spotify refresh tokens and per-user group playlists."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.spotify.models.user_spotify_playlist import UserSpotifyPlaylist


def user_is_linked(user: User) -> bool:
    """True when the user has a stored Spotify refresh token."""
    return bool(user.spotify_refresh_token)


def set_refresh_token(user: User, refresh_token: str) -> None:
    """Store a Spotify refresh token on the user."""
    user.spotify_refresh_token = refresh_token


def clear_refresh_token(user: User) -> None:
    """Forget the user's Spotify refresh token."""
    user.spotify_refresh_token = None


def get_playlist(
    db: Session, user: User, group: Group
) -> UserSpotifyPlaylist | None:
    """Return the stored playlist row for this user and group, if any."""
    return db.scalars(
        select(UserSpotifyPlaylist).where(
            UserSpotifyPlaylist.user_id == user.id,
            UserSpotifyPlaylist.group_id == group.id,
        )
    ).one_or_none()


def upsert_playlist(
    db: Session, user: User, group: Group, playlist_id: str
) -> UserSpotifyPlaylist:
    """Remember the Spotify playlist id for this user and group."""
    row = get_playlist(db, user, group)
    if row is None:
        row = UserSpotifyPlaylist(
            user_id=user.id,
            group_id=group.id,
            spotify_playlist_id=playlist_id,
        )
        db.add(row)
    else:
        row.spotify_playlist_id = playlist_id
    return row
