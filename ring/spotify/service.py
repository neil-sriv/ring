"""Link a Spotify account and write tracks into it."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from sqlalchemy.orm import Session

from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.spotify import client as spotify_client
from ring.spotify import settings as spotify_settings
from ring.spotify.content import (
    group_track_ids,
    letter_track_ids,
    load_group_letters,
    load_letter_with_content,
)
from ring.spotify.crud import account as account_crud
from ring.spotify.errors import (
    SpotifyNotLinkedError,
    SpotifyPlaylistMissingError,
    SpotifyTokenRejectedError,
)


@dataclass(frozen=True)
class PlaylistSync:
    """Result of creating or updating the user's playlist for a group."""

    playlist_id: str
    playlist_url: str
    name: str
    track_count: int


def link_with_authorization_code(db: Session, user: User, code: str) -> None:
    """Exchange an OAuth code and store the refresh token on the user."""
    refresh_token = spotify_client.exchange_authorization_code(code)
    account_crud.set_refresh_token(user, refresh_token)
    db.commit()


def _access_token(db: Session, user: User) -> str:
    stored = user.spotify_refresh_token
    if not stored:
        raise SpotifyNotLinkedError()
    try:
        access_token, rotated = spotify_client.refresh_access_token(stored)
    except SpotifyTokenRejectedError:
        account_crud.clear_refresh_token(user)
        db.commit()
        raise SpotifyNotLinkedError() from None
    if rotated:
        account_crud.set_refresh_token(user, rotated)
        db.commit()
    return access_token


def save_letter_to_library(
    db: Session, user: User, letter: Letter
) -> list[str]:
    """Save the letter's Spotify tracks to the user's library."""
    spotify_settings.require_spotify_app_config()
    loaded = load_letter_with_content(db, letter)
    track_ids = letter_track_ids(loaded)
    if not track_ids:
        if not account_crud.user_is_linked(user):
            raise SpotifyNotLinkedError()
        return []
    access_token = _access_token(db, user)
    spotify_client.save_tracks_to_library(access_token, track_ids)
    logger.info(
        "Saved {} Spotify tracks for {}",
        len(track_ids),
        user.api_identifier,
    )
    return track_ids


def read_group_playlist(
    db: Session, user: User, group: Group
) -> PlaylistSync | None:
    """Return the stored playlist for this user and group, if one exists."""
    spotify_settings.require_spotify_app_config()
    if not account_crud.user_is_linked(user):
        raise SpotifyNotLinkedError()
    row = account_crud.get_playlist(db, user, group)
    if row is None:
        return None
    letters = load_group_letters(db, group)
    track_ids = group_track_ids(letters)
    return PlaylistSync(
        playlist_id=row.spotify_playlist_id,
        playlist_url=spotify_client.playlist_url(row.spotify_playlist_id),
        name=group.name,
        track_count=len(track_ids),
    )


def ensure_group_playlist(
    db: Session, user: User, group: Group
) -> PlaylistSync:
    """Create or update one playlist in the user's Spotify account."""
    spotify_settings.require_spotify_app_config()
    letters = load_group_letters(db, group)
    track_ids = group_track_ids(letters)
    access_token = _access_token(db, user)
    row = account_crud.get_playlist(db, user, group)
    playlist_id = row.spotify_playlist_id if row is not None else None
    if playlist_id is not None:
        try:
            spotify_client.update_playlist_name(
                access_token, playlist_id, group.name
            )
        except SpotifyPlaylistMissingError:
            playlist_id = None
    if playlist_id is None:
        playlist_id = spotify_client.create_playlist(access_token, group.name)
        account_crud.upsert_playlist(db, user, group, playlist_id)
        db.commit()
    try:
        spotify_client.replace_playlist_tracks(
            access_token, playlist_id, track_ids
        )
    except SpotifyPlaylistMissingError:
        playlist_id = spotify_client.create_playlist(access_token, group.name)
        account_crud.upsert_playlist(db, user, group, playlist_id)
        db.commit()
        spotify_client.replace_playlist_tracks(
            access_token, playlist_id, track_ids
        )
    logger.info(
        "Synced Spotify playlist {} for {} in {}",
        playlist_id,
        user.api_identifier,
        group.api_identifier,
    )
    return PlaylistSync(
        playlist_id=playlist_id,
        playlist_url=spotify_client.playlist_url(playlist_id),
        name=group.name,
        track_count=len(track_ids),
    )
