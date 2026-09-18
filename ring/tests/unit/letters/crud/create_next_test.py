"""Tests for the create-next cyclic letter ops helper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from ring.api_identifier.util import IDNotFoundException
from ring.letters.constants import QUESTION_BANK, LetterStatus
from ring.letters.crud.create_next import (
    CreateNextLetterError,
    create_next_cyclic_letter,
)
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestCreateNextCyclicLetter:
    def test_returns_existing_upcoming(self, db_session: Session) -> None:
        group = GroupFactory.create()
        upcoming = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            number=2,
        )
        db_session.commit()

        result = create_next_cyclic_letter(db_session, group.api_identifier)
        assert result is upcoming

    def test_creates_from_in_progress_with_seeded_questions(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        DefaultQuestionFactory.create(group=group, question_text="Photo Wall")
        send_at = datetime.now(tz=UTC) + timedelta(days=5)
        LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            number=24,
            send_at=send_at,
        )
        db_session.commit()

        result = create_next_cyclic_letter(db_session, group.api_identifier)
        db_session.commit()

        assert result.status == LetterStatus.UPCOMING
        assert result.number == 25
        assert result.send_at == send_at + timedelta(days=group.cycle_length)
        texts = [question.question_text for question in result.questions]
        assert "Photo Wall" in texts
        assert sum(text in QUESTION_BANK for text in texts) == 3
        assert all(question.author_id is None for question in result.questions)

    def test_creates_from_latest_sent_when_cadence_is_closed(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) - timedelta(days=10)
        LetterFactory.create(
            group=group,
            status=LetterStatus.SENT,
            number=3,
            send_at=send_at,
        )
        db_session.commit()

        result = create_next_cyclic_letter(db_session, group.api_identifier)
        db_session.commit()

        assert result.status == LetterStatus.UPCOMING
        assert result.number == 4
        assert result.send_at == send_at + timedelta(days=group.cycle_length)

    def test_errors_when_group_has_no_cyclic_letters(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        with pytest.raises(CreateNextLetterError):
            create_next_cyclic_letter(db_session, group.api_identifier)

    def test_errors_when_group_is_missing(self, db_session: Session) -> None:
        with pytest.raises(IDNotFoundException):
            create_next_cyclic_letter(db_session, "grp_does-not-exist")
