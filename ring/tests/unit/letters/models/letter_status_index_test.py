"""Tests for one-upcoming / one-in-progress cyclic letter indexes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus, LetterType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestCyclicLetterStatusIndexes:
    """DB invariants: at most one cyclic letter per live status per group."""

    def test_second_cyclic_upcoming_is_rejected(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) + timedelta(days=10)
        LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            send_at=send_at,
        )
        db_session.commit()

        with pytest.raises(IntegrityError):
            LetterFactory.create(
                group=group,
                status=LetterStatus.UPCOMING,
                send_at=send_at + timedelta(days=30),
            )
        db_session.rollback()

    def test_second_cyclic_in_progress_is_rejected(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
        )
        db_session.commit()

        with pytest.raises(IntegrityError):
            LetterFactory.create(
                group=group,
                status=LetterStatus.IN_PROGRESS,
            )
        db_session.rollback()

    def test_one_upcoming_and_one_in_progress_are_allowed(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
        )
        LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            send_at=datetime.now(tz=UTC) + timedelta(days=20),
        )
        db_session.commit()

        assert len(group.in_progress_letters) == 1
        assert len(group.upcoming_letters) == 1

    def test_multiple_sent_cyclic_letters_are_allowed(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        LetterFactory.create(group=group, status=LetterStatus.SENT, number=1)
        LetterFactory.create(group=group, status=LetterStatus.SENT, number=2)
        db_session.commit()

        assert (
            len(
                [
                    letter
                    for letter in group.cyclic_letters
                    if letter.status == LetterStatus.SENT
                ]
            )
            == 2
        )

    def test_adhoc_letters_are_not_limited_by_cyclic_indexes(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
        )
        LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
        )
        db_session.commit()

        adhoc = [
            letter
            for letter in group.letters
            if letter.letter_type == LetterType.ADHOC
        ]
        assert len(adhoc) == 2
