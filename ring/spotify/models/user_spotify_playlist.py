"""Spotify playlist id stored for one user and one group.

The playlist lives in that user's Spotify account. Ring remembers the id so
a later sync updates the same playlist instead of creating another one.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


class UserSpotifyPlaylist(Base, CreatedAtMixin):
    """Playlist id in the current user's Spotify account for a group."""

    __tablename__ = "user_spotify_playlist"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("group.id"), nullable=False, index=True
    )
    spotify_playlist_id: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "group_id",
            name="uq_user_group_spotify_playlist",
        ),
    )
