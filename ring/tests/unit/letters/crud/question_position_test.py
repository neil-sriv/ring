"""Tests for question display-order positions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session

from ring.letters.constants import (
    DEFAULT_QUESTIONS,
    QUESTION_BANK,
    LetterStatus,
)
from ring.letters.crud import letter as letter_crud
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestQuestionPosition:
    def test_create_letter_positions_bank_then_defaults(
        self, db_session: Session, faker: Faker
    ) -> None:
        group = GroupFactory.create()
        send_at = faker.date_time(tzinfo=UTC)
        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        ordered = sorted(letter.questions, key=lambda q: q.position)
        assert [q.position for q in ordered] == list(range(len(ordered)))
        default_count = len(DEFAULT_QUESTIONS)
        assert all(
            q.question_text in QUESTION_BANK for q in ordered[:-default_count]
        )
        assert [
            q.question_text for q in ordered[-default_count:]
        ] == DEFAULT_QUESTIONS
        assert len(ordered) == default_count + 3

    def test_member_added_question_inserts_before_seeded(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        letter = letter_crud.create_letter_with_questions(
            db_session,
            group.api_identifier,
            datetime.now(tz=UTC),
        )
        db_session.commit()
        author = UserFactory.create()
        added = letter_crud.add_question(
            db_session, letter, "Member question", author=author
        )
        db_session.commit()

        assert added.position == 0
        assert added.author == author
        assert added.added_late is False

    def test_group_bank_comes_before_defaults(
        self, db_session: Session, faker: Faker
    ) -> None:
        group = GroupFactory.create()
        defaults = [
            DefaultQuestionFactory.create(
                group=group, question_text=f"Default {i}"
            )
            for i in range(2)
        ]
        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, faker.date_time(tzinfo=UTC)
        )
        db_session.commit()

        ordered = sorted(letter.questions, key=lambda q: q.position)
        assert [q.question_text for q in ordered[-2:]] == [
            default.question_text for default in defaults
        ]
        assert all(q.question_text in QUESTION_BANK for q in ordered[:-2])

    def test_compile_letter_dict_follows_position(
        self, db_session: Session
    ) -> None:
        letter = LetterFactory.create()
        later = letter_crud.add_question(db_session, letter, "Second")
        earlier = letter_crud.add_question(db_session, letter, "First")
        later.position = 1
        earlier.position = 0
        db_session.commit()

        compiled = letter_crud.compile_letter_dict(letter)
        assert list(compiled.keys()) == ["First", "Second"]

    def test_loop_specific_questions_come_before_group_defaults(
        self, db_session: Session, faker: Faker
    ) -> None:
        group = GroupFactory.create()
        defaults = [
            DefaultQuestionFactory.create(
                group=group, question_text=f"Default {i}"
            )
            for i in range(2)
        ]
        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, faker.date_time(tzinfo=UTC)
        )
        db_session.commit()
        author = UserFactory.create()
        letter_crud.add_question(
            db_session, letter, "Extra first", author=author
        )
        letter_crud.add_question(
            db_session, letter, "Extra second", author=author
        )
        db_session.commit()

        ordered = sorted(letter.questions, key=lambda q: q.position)
        assert [q.question_text for q in ordered[:2]] == [
            "Extra first",
            "Extra second",
        ]
        assert [q.question_text for q in ordered[-2:]] == [
            default.question_text for default in defaults
        ]
        assert [q.position for q in ordered] == list(range(len(ordered)))
        assert all(question.added_late is False for question in ordered)

    def test_in_progress_late_questions_lead_in_add_order(
        self, db_session: Session
    ) -> None:
        group = GroupFactory.create()
        letter = letter_crud.create_letter_with_questions(
            db_session,
            group.api_identifier,
            datetime.now(tz=UTC) + timedelta(days=3),
        )
        author = UserFactory.create()
        earlier = letter_crud.add_question(
            db_session, letter, "Earlier authored", author=author
        )
        seeded_order = [
            question.question_text
            for question in sorted(letter.questions, key=lambda q: q.position)
            if question.author is None
        ]
        letter.status = LetterStatus.IN_PROGRESS
        first = letter_crud.add_question(
            db_session, letter, "Late one", author=author
        )
        second = letter_crud.add_question(
            db_session, letter, "Late two", author=author
        )
        unauthored = letter_crud.add_question(
            db_session, letter, "Late unauthored"
        )
        db_session.commit()

        ordered = sorted(letter.questions, key=lambda q: q.position)
        assert [question.question_text for question in ordered[:3]] == [
            "Late one",
            "Late two",
            "Late unauthored",
        ]
        assert first.position == 0 and first.added_late is True
        assert second.position == 1 and second.added_late is True
        assert unauthored.position == 2 and unauthored.added_late is True
        assert earlier.added_late is False
        non_late = [
            question.question_text
            for question in ordered
            if not question.added_late
        ]
        assert non_late == ["Earlier authored", *seeded_order]
        assert [question.position for question in ordered] == list(
            range(len(ordered))
        )

    def test_existing_questions_default_added_late_false(
        self, db_session: Session
    ) -> None:
        """Rows that omit added_late read back as false.

        The migration adds the column NOT NULL with server default false,
        which is what backfills questions that already exist.
        """
        letter = LetterFactory.create()
        created = QuestionFactory.create(
            letter=letter, question_text="Created without the flag"
        )
        db_session.commit()
        assert created.added_late is False
        api_identifier = f"qstn_{uuid4()}"
        db_session.execute(
            text(
                "INSERT INTO question "
                "(api_identifier, question_text, letter_id) "
                "VALUES (:api_identifier, :question_text, :letter_id)"
            ),
            {
                "api_identifier": api_identifier,
                "question_text": "Already on the letter",
                "letter_id": letter.id,
            },
        )
        db_session.commit()

        added_late = db_session.execute(
            text(
                "SELECT added_late FROM question "
                "WHERE api_identifier = :api_identifier"
            ),
            {"api_identifier": api_identifier},
        ).scalar_one()
        assert added_late is False
