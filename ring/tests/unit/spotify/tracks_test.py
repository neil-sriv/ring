"""Spotify track id extraction from letter text."""

from __future__ import annotations

from ring.spotify.tracks import (
    extract_spotify_track_ids,
    extract_spotify_track_ids_from_parts,
)

TRACK_A = "a" * 22
TRACK_B = "b" * 22
TRACK_C = "c" * 22


def test_open_spotify_link_query_and_case() -> None:
    text = (
        f"Listen https://open.spotify.com/track/{TRACK_A}?si=abc "
        f"and HTTPS://OPEN.SPOTIFY.COM/TRACK/{TRACK_B}"
    )
    assert extract_spotify_track_ids(text) == [TRACK_A, TRACK_B]


def test_embed_and_intl_links() -> None:
    text = (
        f"https://open.spotify.com/embed/track/{TRACK_A}\n"
        f"https://open.spotify.com/intl-de/track/{TRACK_B}\n"
        f"https://open.spotify.com/embed/intl-en/track/{TRACK_C}"
    )
    assert extract_spotify_track_ids(text) == [TRACK_A, TRACK_B, TRACK_C]


def test_spotify_uri_and_dedupe() -> None:
    text = (
        f"spotify:track:{TRACK_A} and again "
        f"https://open.spotify.com/track/{TRACK_A}"
    )
    assert extract_spotify_track_ids(text) == [TRACK_A]


def test_ignores_albums_and_short_ids() -> None:
    text = (
        f"https://open.spotify.com/album/{TRACK_A} "
        "https://open.spotify.com/track/tooshort "
        "spotify:album:" + TRACK_B
    )
    assert extract_spotify_track_ids(text) == []


def test_parts_skip_empty_and_keep_order() -> None:
    ids = extract_spotify_track_ids_from_parts(
        [
            None,
            f"spotify:track:{TRACK_B}",
            "",
            f"https://open.spotify.com/track/{TRACK_A}",
        ]
    )
    assert ids == [TRACK_B, TRACK_A]
