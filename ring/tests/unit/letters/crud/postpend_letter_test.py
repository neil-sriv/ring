"""Tests for postpend letter behavior with send thresholds."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.send_threshold import (
    LETTER_SEND_DEFERRAL_DAYS,
    defer_letter_send_if_below_threshold,
    hold_letter_for_send_threshold,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestPostpendLetters:
    """Tests for postpend_upcoming_letters threshold handling."""

    def run_postpend_job(
        self, db_session: Session, letter_ids: list[int]
    ) -> None:
        letter_crud.postpend_upcoming_letters_with_session(
            db_session, letter_ids
        )

    def test_postpend_defers_when_responders_below_threshold(
        self, db_session: Session
    ) -> None:
        """Do not mark SENT when threshold is unmet; defer send instead."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        self.run_postpend_job(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_postpend_does_not_defer_before_send_date(
        self, db_session: Session
    ) -> None:
        """Leave the send date alone when the deadline has not arrived yet."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=5)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        self.run_postpend_job(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at

    def test_repeated_postpend_polls_defer_send_date_once(
        self, db_session: Session
    ) -> None:
        """Deferring once moves the deadline out of reach of later polls."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        for _ in range(3):
            self.run_postpend_job(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_send_email_and_postpend_defer_send_date_once(
        self, db_session: Session
    ) -> None:
        """At deadline, send-email and postpend must not stack two deferrals."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        assert defer_letter_send_if_below_threshold(db_session, letter) is True
        assert hold_letter_for_send_threshold(db_session, letter) is True
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

        self.run_postpend_job(db_session, [letter.id])
        db_session.refresh(letter)

        assert letter.status == LetterStatus.SENT
