"""Cadence invariants modeled on the texas exes #24 production incident.

A skipped cyclic number plus a recovery-created in-progress letter that
only had group defaults used to: collide on ``unique_group_letter_number``,
leave the group without an upcoming successor, and omit the 3 bank
questions. These tests lock the contract that promote, edit-to-in-progress,
and ``create_letter_with_questions`` must satisfy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from ring.letters.constants import QUESTION_BANK, LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory

TEXAS_EXES_DEFAULTS = (
    "📸 Photo Wall",
    "🌤️ One Good Thing",
    "💭 On Your Mind",
    "👀 Check it Out",
)
# 1-15 and 17-23 exist; 16 is the gap; 24 is the live letter.
HISTORICAL_NUMBERS = tuple(range(1, 16)) + tuple(range(17, 24))


def _seed_gapped_history(group: Group) -> None:
    send_base = datetime(2024, 8, 1, tzinfo=UTC)
    for number in HISTORICAL_NUMBERS:
        LetterFactory.create(
            group=group,
            status=LetterStatus.SENT,
            number=number,
            send_at=send_base + timedelta(days=30 * number),
        )


def _texas_exes_like_group(
    db_session: Session,
    *,
    live_status: LetterStatus = LetterStatus.IN_PROGRESS,
) -> tuple[Group, Letter]:
    group = GroupFactory.create()
    for text in TEXAS_EXES_DEFAULTS:
        DefaultQuestionFactory.create(group=group, question_text=text)
    _seed_gapped_history(group)
    live_send_at = datetime.now(tz=UTC) + timedelta(days=6)
    live = LetterFactory.create(
        group=group,
        status=live_status,
        number=24,
        send_at=live_send_at,
    )
    for text in TEXAS_EXES_DEFAULTS:
        QuestionFactory.create(letter=live, question_text=text, author=None)
    db_session.commit()
    return group, live


def _assert_seeded_successor(letter: Letter, group: Group) -> None:
    default_texts = [
        question.question_text for question in group.default_questions
    ]
    texts = [question.question_text for question in letter.questions]
    for default_text in default_texts:
        assert default_text in texts
    assert sum(text in QUESTION_BANK for text in texts) == 3
    assert len(letter.questions) == len(default_texts) + 3
    assert all(question.author_id is None for question in letter.questions)
    assert letter.status == LetterStatus.UPCOMING
    assert letter.number == 25
    assert letter.send_at == group.in_progress_letters[-1].send_at + timedelta(
        days=group.cycle_length
    )


class TestCadenceInvariants:
    def test_heal_in_progress_without_upcoming_uses_max_plus_one(
        self, db_session: Session
    ) -> None:
        group, live = _texas_exes_like_group(db_session)
        assert group.upcoming_letters == []
        assert live.number == 24
        assert len(live.questions) == 4

        with patch(
            "ring.async_scheduler.scheduler.scheduler",
            MagicMock(),
        ):
            letter_crud.promote_and_create_new_letters_with_session(
                db_session, [live.id]
            )

        db_session.expire_all()
        refreshed = db_session.get(Letter, live.id)
        assert refreshed is not None
        assert refreshed.status == LetterStatus.IN_PROGRESS
        upcoming = [
            letter
            for letter in letter_crud.get_letters(
                db_session, group.api_identifier
            )
            if letter.status == LetterStatus.UPCOMING
        ]
        assert len(upcoming) == 1
        _assert_seeded_successor(upcoming[0], refreshed.group)

    def test_edit_to_in_progress_queues_seeded_successor(
        self, db_session: Session
    ) -> None:
        group, live = _texas_exes_like_group(
            db_session, live_status=LetterStatus.UPCOMING
        )

        letter_crud.edit_letter(
            db_session, live, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()
        db_session.expire_all()

        edited = db_session.get(Letter, live.id)
        assert edited is not None
        assert edited.status == LetterStatus.IN_PROGRESS
        upcoming = [
            letter
            for letter in letter_crud.get_letters(
                db_session, group.api_identifier
            )
            if letter.status == LetterStatus.UPCOMING
        ]
        assert len(upcoming) == 1
        _assert_seeded_successor(upcoming[0], edited.group)

    def test_create_letter_with_questions_skips_number_gap(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        for text in TEXAS_EXES_DEFAULTS:
            DefaultQuestionFactory.create(group=group, question_text=text)
        _seed_gapped_history(group)
        db_session.commit()

        send_at = datetime.now(tz=UTC) + timedelta(days=20)
        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.number == 24
        assert letter.status == LetterStatus.UPCOMING
        texts = [question.question_text for question in letter.questions]
        assert all(text in texts for text in TEXAS_EXES_DEFAULTS)
        assert sum(text in QUESTION_BANK for text in texts) == 3
        assert all(question.author_id is None for question in letter.questions)

    def test_promote_upcoming_with_gap_creates_one_successor(
        self, db_session: Session
    ) -> None:
        group, live = _texas_exes_like_group(
            db_session, live_status=LetterStatus.UPCOMING
        )

        with patch(
            "ring.async_scheduler.scheduler.scheduler",
            MagicMock(),
        ):
            letter_crud.promote_and_create_new_letters_with_session(
                db_session, [live.id]
            )

        db_session.expire_all()
        upcoming = [
            letter
            for letter in letter_crud.get_letters(
                db_session, group.api_identifier
            )
            if letter.status == LetterStatus.UPCOMING
        ]
        assert len(upcoming) == 1
        promoted = db_session.get(Letter, live.id)
        assert promoted is not None
        assert promoted.status == LetterStatus.IN_PROGRESS
        _assert_seeded_successor(upcoming[0], promoted.group)
