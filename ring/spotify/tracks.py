"""Find Spotify track ids in letter text.

Recognizes open.spotify.com track links (including embed and intl paths)
and spotify:track URIs. There is no dedicated song column on letters;
question text, response text, and the letter title are the content.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_TRACK_ID = r"[0-9A-Za-z]{22}"
_TRACK_RE = re.compile(
    rf"https?://open\.spotify\.com/(?:embed/)?"
    rf"(?:intl-[a-z0-9-]+/)?track/({_TRACK_ID})"
    rf"|spotify:track:({_TRACK_ID})",
    re.IGNORECASE,
)


def extract_spotify_track_ids(text: str) -> list[str]:
    """Return unique track ids in the order they first appear."""
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for match in _TRACK_RE.finditer(text):
        track_id = next(group for group in match.groups() if group)
        if track_id not in seen:
            seen.add(track_id)
            found.append(track_id)
    return found


def extract_spotify_track_ids_from_parts(
    parts: Iterable[str | None],
) -> list[str]:
    """Extract track ids from several text fields, preserving order."""
    return extract_spotify_track_ids("\n".join(part for part in parts if part))
