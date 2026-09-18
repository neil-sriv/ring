"""Tests for question display-order positions."""

from __future__ import annotations

from datetime import UTC, datetime

from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import DEFAULT_QUESTIONS, QUESTION_BANK
from ring.letters.crud import letter as letter_crud
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestQuestionPosition:
    def test_create_letter_positions_defaults_then_bank(
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
        assert [
            q.question_text for q in ordered[:default_count]
        ] == DEFAULT_QUESTIONS
        assert all(
            q.question_text in QUESTION_BANK for q in ordered[default_count:]
        )
        assert len(ordered) == default_count + 3

    def test_member_added_question_appends(self, db_session: Session) -> None:
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

        assert added.position == len(letter.questions) - 1
        assert added.author == author

    def test_group_defaults_come_before_bank(
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
        assert [q.question_text for q in ordered[:2]] == [
            default.question_text for default in defaults
        ]
        assert all(q.question_text in QUESTION_BANK for q in ordered[2:])

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
