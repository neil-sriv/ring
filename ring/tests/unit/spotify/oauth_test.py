"""OAuth state and return-path checks."""

from __future__ import annotations

from ring.spotify.oauth import (
    create_oauth_state,
    decode_oauth_state,
    safe_oauth_error,
    safe_return_path,
)


def test_safe_return_path_rejects_off_site_targets() -> None:
    assert safe_return_path("/loops/lttr_1?spotify_action=save") == (
        "/loops/lttr_1?spotify_action=save"
    )
    assert safe_return_path("https://evil.example/phish") == "/"
    assert safe_return_path("//evil.example") == "/"
    assert safe_return_path("/\\evil") == "/"
    assert safe_return_path("loops/relative") == "/"


def test_state_round_trip_sanitizes_return_path() -> None:
    state = create_oauth_state("usr_123", "https://evil.example/steal")
    user_api_id, return_to = decode_oauth_state(state)
    assert user_api_id == "usr_123"
    assert return_to == "/"


def test_state_preserves_in_app_path() -> None:
    path = "/groups/grp_1/loops?spotify_action=playlist"
    state = create_oauth_state("usr_abc", path)
    assert decode_oauth_state(state) == ("usr_abc", path)


def test_safe_oauth_error_limits_untrusted_text() -> None:
    assert safe_oauth_error("access_denied") == "access_denied"
    assert safe_oauth_error("bad error") == "denied"
    assert safe_oauth_error(None) == "denied"
    assert safe_oauth_error("x" * 65) == "denied"
