"""Tests for postpend letter behavior with send thresholds."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.send_threshold import LETTER_SEND_DEFERRAL_DAYS
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestPostpendLetters:
    """Tests for postpend_upcoming_letters threshold handling."""

    def test_postpend_defers_when_responders_below_threshold(
        self, db_session: Session
    ) -> None:
        """Do not mark SENT when threshold is unmet; defer send instead."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        letter_crud.postpend_upcoming_letters(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_postpend_marks_sent_when_threshold_met(
        self, db_session: Session
    ) -> None:
        """Mark SENT when enough participants have responded."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        ResponseFactory.create(question=question, participant=members[1])
        db_session.commit()

        letter_crud.postpend_upcoming_letters(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.SENT
