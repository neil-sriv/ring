"""Tests for short link CRUD helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.links.crud import short_link as short_link_crud
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestShortLinkCrud:
    """Test suite for short link CRUD operations."""

    def test_create_short_link_generates_token(
        self, db_session: Session
    ) -> None:
        """Creating a short link assigns a unique, non-empty token."""
        creator = UserFactory.create()
        letter = LetterFactory.create()
        db_session.commit()

        link = short_link_crud.create_short_link(
            db_session, letter.api_identifier, creator
        )
        db_session.commit()

        assert link.token
        assert (
            short_link_crud.get_short_link_by_token(db_session, link.token)
            is link
        )

    def test_create_short_link_reuses_existing(
        self, db_session: Session
    ) -> None:
        """Two creates for the same target/creator return the same row."""
        creator = UserFactory.create()
        letter = LetterFactory.create()
        db_session.commit()

        first = short_link_crud.create_short_link(
            db_session, letter.api_identifier, creator
        )
        db_session.commit()
        second = short_link_crud.create_short_link(
            db_session, letter.api_identifier, creator
        )
        db_session.commit()

        assert first.id == second.id
        assert first.token == second.token

    def test_create_short_link_distinct_per_creator(
        self, db_session: Session
    ) -> None:
        """Different creators get distinct links for the same target."""
        letter = LetterFactory.create()
        creator_a = UserFactory.create()
        creator_b = UserFactory.create()
        db_session.commit()

        link_a = short_link_crud.create_short_link(
            db_session, letter.api_identifier, creator_a
        )
        link_b = short_link_crud.create_short_link(
            db_session, letter.api_identifier, creator_b
        )
        db_session.commit()

        assert link_a.id != link_b.id
        assert link_a.token != link_b.token
