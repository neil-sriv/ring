from __future__ import annotations

from ring.letters.constants import LetterStatus
from ring.search.query import expand_author_me, parse_search_query


class TestParseSearchQuery:
    def test_plain_text_is_unchanged(self) -> None:
        parsed = parse_search_query("sunset photos")
        assert parsed.text == "sunset photos"
        assert parsed.authors == ()
        assert parsed.statuses == ()
        assert parsed.match_nothing is False

    def test_author_and_remaining_text(self) -> None:
        parsed = parse_search_query("quokka author:Zelda habits")
        assert parsed.text == "quokka habits"
        assert parsed.authors == ("Zelda",)

    def test_quoted_author_name(self) -> None:
        parsed = parse_search_query('author:"Zelda Quokka" sunset')
        assert parsed.text == "sunset"
        assert parsed.authors == ("Zelda Quokka",)

    def test_status_aliases(self) -> None:
        assert parse_search_query("status:open").statuses == (
            LetterStatus.IN_PROGRESS,
        )
        assert parse_search_query("status:published").statuses == (
            LetterStatus.SENT,
        )
        assert parse_search_query("status:upcoming").statuses == (
            LetterStatus.UPCOMING,
        )
        assert parse_search_query("is:open").statuses == (
            LetterStatus.IN_PROGRESS,
        )

    def test_raw_letter_status_value(self) -> None:
        parsed = parse_search_query("status:IN_PROGRESS")
        assert parsed.statuses == (LetterStatus.IN_PROGRESS,)

    def test_invalid_status_matches_nothing(self) -> None:
        parsed = parse_search_query("status:nope")
        assert parsed.statuses == ()
        assert parsed.match_nothing is True

    def test_qualifier_only_has_empty_text(self) -> None:
        parsed = parse_search_query("author:jane")
        assert parsed.text == ""
        assert parsed.authors == ("jane",)

    def test_key_inside_another_token_is_plain_text(self) -> None:
        """A qualifier key only counts at the start of a token."""
        for query in (
            "this:open",
            "coauthor:jane",
            "basis:published",
            "camping this:open",
        ):
            parsed = parse_search_query(query)
            assert parsed.text == query, query
            assert parsed.authors == (), query
            assert parsed.statuses == (), query
            assert parsed.match_nothing is False, query

    def test_expand_author_me(self) -> None:
        expanded = expand_author_me("notes author:@me", "jane@example.com")
        assert expanded == 'notes author:"jane@example.com"'
