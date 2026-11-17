"""Tests for question display-order positions."""

from __future__ import annotations

from datetime import UTC, datetime

from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import DEFAULT_QUESTIONS, QUESTION_BANK
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def _ordered(letter: Letter) -> list[Question]:
    return sorted(letter.questions, key=lambda q: q.position)


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

        ordered = _ordered(letter)
        default_count = len(DEFAULT_QUESTIONS)
        assert [q.position for q in ordered] == list(range(len(ordered)))
        assert len(ordered) == default_count + 3
        assert all(
            q.question_text in QUESTION_BANK
            for q in ordered[: len(ordered) - default_count]
        )
        assert [
            q.question_text for q in ordered[-default_count:]
        ] == DEFAULT_QUESTIONS

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

        ordered = _ordered(letter)
        assert added.position == 0
        assert added.author == author
        assert ordered[0] is added
        assert [q.position for q in ordered] == list(range(len(ordered)))

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
        first = letter_crud.add_question(
            db_session, letter, "Extra first", author=author
        )
        second = letter_crud.add_question(
            db_session, letter, "Extra second", author=author
        )
        db_session.commit()

        ordered = _ordered(letter)
        default_texts = [default.question_text for default in defaults]
        extra_positions = [first.position, second.position]
        default_positions = [
            question.position
            for question in ordered
            if question.question_text in default_texts
        ]
        bank_positions = [
            question.position
            for question in ordered
            if question.question_text in QUESTION_BANK
        ]

        assert [q.question_text for q in ordered[:2]] == [
            "Extra first",
            "Extra second",
        ]
        assert [q.question_text for q in ordered[-2:]] == default_texts
        assert max(extra_positions) < min(bank_positions)
        assert max(bank_positions) < min(default_positions)
        assert [q.position for q in ordered] == list(range(len(ordered)))

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

        ordered = _ordered(letter)
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
