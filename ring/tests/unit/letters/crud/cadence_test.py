"""Tests for the shared cyclic-letter cadence owner."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from ring.letters.constants import QUESTION_BANK, LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestAdvanceCyclicLetter:
    """``advance_cyclic_letter`` is the single successor-creation path."""

    def test_returns_existing_upcoming_without_creating(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        in_progress = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            number=1,
        )
        upcoming = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            number=2,
        )
        db_session.commit()

        result = letter_crud.advance_cyclic_letter(
            db_session, group, after=in_progress
        )
        db_session.commit()

        assert result is upcoming
        assert (
            len(
                [
                    letter
                    for letter in letter_crud.get_letters(
                        db_session, group.api_identifier
                    )
                    if letter.status == LetterStatus.UPCOMING
                ]
            )
            == 1
        )

    def test_creates_successor_from_in_progress_when_after_omitted(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) + timedelta(days=4)
        LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            number=3,
            send_at=send_at,
        )
        db_session.commit()

        result = letter_crud.advance_cyclic_letter(db_session, group)
        db_session.commit()

        assert result is not None
        assert result.status == LetterStatus.UPCOMING
        assert result.number == 4
        assert result.send_at == send_at + timedelta(days=group.cycle_length)

    def test_creates_successor_after_sent_letter_without_in_progress(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        sent = LetterFactory.create(
            group=group,
            status=LetterStatus.SENT,
            number=5,
            send_at=send_at,
        )
        db_session.commit()

        result = letter_crud.advance_cyclic_letter(
            db_session, group, after=sent
        )
        db_session.commit()

        assert result is not None
        assert result.status == LetterStatus.UPCOMING
        assert result.number == 6
        assert result.send_at == send_at + timedelta(days=group.cycle_length)
        assert group.in_progress_letters == []

    def test_returns_none_without_source_or_upcoming(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        assert letter_crud.advance_cyclic_letter(db_session, group) is None

    def test_successor_seeds_group_defaults_and_bank_questions(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        defaults = [
            DefaultQuestionFactory.create(group=group, question_text=text)
            for text in ("Photo Wall", "One Good Thing")
        ]
        LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            number=1,
        )
        db_session.commit()

        successor = letter_crud.advance_cyclic_letter(db_session, group)
        db_session.commit()

        assert successor is not None
        texts = [question.question_text for question in successor.questions]
        for default in defaults:
            assert default.question_text in texts
        bank_count = sum(text in QUESTION_BANK for text in texts)
        assert bank_count == 3
        assert len(successor.questions) == len(defaults) + 3
        assert all(
            question.author_id is None for question in successor.questions
        )

    def test_postpend_uses_advance_after_send(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            number=8,
            send_at=send_at,
        )
        db_session.commit()

        with patch(
            "ring.letters.crud.letter.send_letter_email", return_value=True
        ):
            letter_crud.postpend_upcoming_letters_with_session(
                db_session, [letter.id]
            )

        db_session.expire_all()
        upcoming = [
            group_letter
            for group_letter in letter_crud.get_letters(
                db_session, group.api_identifier
            )
            if group_letter.status == LetterStatus.UPCOMING
        ]
        assert len(upcoming) == 1
        assert upcoming[0].number == 9

    def test_promote_and_edit_share_advance(self, db_session: Session) -> None:
        from ring.letters.crud.letter import advance_cyclic_letter

        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) + timedelta(days=3)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            number=1,
            send_at=send_at,
        )
        db_session.commit()

        with (
            patch(
                "ring.async_scheduler.scheduler.scheduler",
                MagicMock(),
            ),
            patch(
                "ring.letters.crud.letter.advance_cyclic_letter",
                wraps=advance_cyclic_letter,
            ) as mock_advance,
        ):
            letter_crud.promote_and_create_new_letters_with_session(
                db_session, [letter.id]
            )
            assert mock_advance.called

        other = GroupFactory.create()
        other_letter = LetterFactory.create(
            group=other,
            status=LetterStatus.UPCOMING,
            send_at=datetime.now(tz=UTC) + timedelta(days=10),
        )
        db_session.commit()

        with patch(
            "ring.letters.crud.letter.advance_cyclic_letter",
            wraps=advance_cyclic_letter,
        ) as mock_advance:
            letter_crud.edit_letter(
                db_session, other_letter, status=LetterStatus.IN_PROGRESS
            )
            assert mock_advance.called
