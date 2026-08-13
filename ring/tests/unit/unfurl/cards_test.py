"""Tests for picking preview copy from a shared path."""

from __future__ import annotations

from ring.unfurl.cards import SITE_CARD, card_for_path


class TestCardForPath:
    """Test suite for `card_for_path`."""

    def test_letter_path_gets_letter_copy(self) -> None:
        card = card_for_path("/loops/lttr_abc123")

        assert card != SITE_CARD
        assert card.title == "A newsletter on Ring"

    def test_invite_path_gets_invite_copy(self) -> None:
        assert card_for_path("/register/some-token").title == (
            "Your invitation to Ring"
        )

    def test_nested_group_path_gets_group_copy(self) -> None:
        assert card_for_path("/groups/grp_abc123/loops").title == (
            "A group on Ring"
        )

    def test_leading_and_trailing_slashes_do_not_matter(self) -> None:
        assert card_for_path("loops/lttr_abc123/") == card_for_path(
            "/loops/lttr_abc123"
        )

    def test_root_path_gets_the_site_card(self) -> None:
        assert card_for_path("/") == SITE_CARD
        assert card_for_path("") == SITE_CARD

    def test_unknown_path_gets_the_site_card(self) -> None:
        assert card_for_path("/settings") == SITE_CARD

    def test_prefix_only_matches_whole_segments(self) -> None:
        """`/loopside` is not a letter, so it must not claim letter copy."""
        assert card_for_path("/loopside") == SITE_CARD
