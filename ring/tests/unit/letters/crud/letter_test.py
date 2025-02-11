from datetime import UTC, datetime, timedelta

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.letters.constants import (
    DEFAULT_QUESTIONS,
    QUESTION_BANK,
    LetterStatus,
)
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.tasks.models.task_model import TaskType
from ring.tests.factories.letters.default_question_factory import (
    DefaultQuestionFactory,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestLetterCrud:
    def test_get_letters(self, db_session: Session, faker: Faker) -> None:
        group = GroupFactory.create()
        letters = [
            LetterFactory.create(group=group, status=LetterStatus.IN_PROGRESS),
            LetterFactory.create(group=group, status=LetterStatus.UPCOMING),
        ]
        db_session.commit()

        assert (
            letter_crud.get_letters(db_session, group.api_identifier)
            == letters
        )

    def test_get_letters_for_user(self, db_session: Session) -> None:
        user = UserFactory.create()
        admin = UserFactory.create()
        groups = [
            GroupFactory.create(admin=admin, members=[admin, user])
            for _ in range(3)
        ]
        letters = [LetterFactory.create(group=g) for g in groups]
        db_session.commit()

        assert letter_crud.get_letters_for_user(db_session, user) == letters

    def test_create_letter(self, db_session: Session, faker: Faker) -> None:
        group = GroupFactory.create()
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        letter = letter_crud.create_letter(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert letter.questions == []
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

        assert letter.number == 1

        [send_email_task, reminder_email_task] = group.schedule.tasks
        assert send_email_task.type == TaskType.SEND_EMAIL
        assert send_email_task.execute_at == send_at

        assert reminder_email_task.type == TaskType.REMINDER_EMAIL
        assert reminder_email_task.execute_at == send_at - timedelta(days=1)

        letter_2 = letter_crud.create_letter(
            db_session,
            group.api_identifier,
            send_at,
            letter_status=LetterStatus.IN_PROGRESS,
        )
        db_session.commit()

        assert letter_2.number == 2
        assert letter_2.status == LetterStatus.IN_PROGRESS

    def test_create_letter_with_questions(
        self, db_session: Session, faker: Faker
    ) -> None:
        group = GroupFactory.create()
        send_at = faker.date_time(tzinfo=UTC)

        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert all(
            [
                q.question_text in QUESTION_BANK + DEFAULT_QUESTIONS
                for q in letter.questions
            ]
        )
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

    def test_create_letter_with_questions_group_default_questions(
        self, db_session: Session, faker: Faker
    ) -> None:
        group = GroupFactory.create()
        default_questions = [
            DefaultQuestionFactory.create(group=group),
        ]
        send_at = faker.date_time(tzinfo=UTC)

        letter = letter_crud.create_letter_with_questions(
            db_session, group.api_identifier, send_at
        )
        db_session.commit()

        assert letter.group == group
        assert letter.send_at == send_at
        assert letter.status == LetterStatus.UPCOMING
        assert letter.participants == group.members
        assert all(
            [
                q.question_text
                in QUESTION_BANK
                + [dq.question_text for dq in default_questions]
                for q in letter.questions
            ]
        )
        assert letter.id is not None
        assert letter.created_at is not None
        assert letter.api_identifier.startswith(Letter.API_ID_PREFIX)

    def test_edit_letter(self, db_session: Session, faker: Faker) -> None:
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        new_send_at = datetime.now(tz=UTC) + timedelta(days=30)

        edited_letter = letter_crud.edit_letter(
            db_session, letter, new_send_at
        )
        db_session.commit()

        assert edited_letter.send_at == new_send_at

        [send_email_task, reminder_email_task] = group.schedule.tasks
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task.execute_at == new_send_at - timedelta(
            days=1
        )

    def test_upsert_letter_tasks(self, db_session: Session) -> None:
        send_at = datetime.now(tz=UTC) + timedelta(days=2)
        letter = LetterFactory.create(send_at=send_at)
        db_session.commit()

        [send_email_task, reminder_email_task] = letter.group.schedule.tasks
        assert send_email_task.execute_at == letter.send_at
        assert reminder_email_task.execute_at == letter.send_at - timedelta(
            days=1
        )

        new_send_at = datetime.now(tz=UTC) + timedelta(days=30)

        letter_crud.upsert_letter_tasks(db_session, letter, new_send_at)
        db_session.commit()

        [send_email_task, reminder_email_task] = letter.group.schedule.tasks
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task.execute_at == new_send_at - timedelta(
            days=1
        )

        letter.send_at = new_send_at
        letter.status = LetterStatus.UPCOMING
        db_session.commit()

        letter_crud.upsert_letter_tasks(db_session, letter, new_send_at)
        db_session.commit()

        [send_email_task, reminder_email_task_1, reminder_email_task_2] = (
            letter.group.schedule.tasks
        )
        assert send_email_task.execute_at == new_send_at
        assert reminder_email_task_1.execute_at == new_send_at - timedelta(
            days=1
        )
        assert reminder_email_task_2.execute_at == new_send_at - timedelta(
            days=8
        )

    def test_add_question(self, db_session: Session, faker: Faker) -> None:
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        author = UserFactory.create()
        db_session.commit()

        question_text = faker.sentence()
        letter_crud.add_question(
            db_session, letter, question_text, author=author
        )
        db_session.commit()

        assert any(
            [q.question_text == question_text for q in letter.questions]
        )

        db_question = db_session.scalars(
            sqlalchemy.select(Question).filter(
                Question.question_text == question_text
            )
        ).one()
        assert db_question.author == author

    def test_add_default_questions(self, db_session: Session) -> None:
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        letter_crud.add_default_questions(db_session, letter)
        db_session.commit()

        assert all(
            [q.question_text in DEFAULT_QUESTIONS for q in letter.questions]
        )
        assert len(letter.questions) == len(DEFAULT_QUESTIONS)
        assert all(q.author is None for q in letter.questions)

    def test_add_random_questions(self, db_session: Session) -> None:
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        letter_crud.add_random_questions(db_session, letter)
        db_session.commit()

        assert all(
            [q.question_text in QUESTION_BANK for q in letter.questions]
        )
        assert len(letter.questions) == 3
        assert all(q.author is None for q in letter.questions)

        letter_crud.add_random_questions(db_session, letter, num_questions=5)
        db_session.commit()

        assert all(
            [q.question_text in QUESTION_BANK for q in letter.questions]
        )
        assert len(letter.questions) == 8
        assert all(q.author is None for q in letter.questions)

    def test_compile_letter_dict(self, db_session: Session) -> None:
        group = GroupFactory.create()
        members = [UserFactory.create() for _ in range(4)]
        for member in members:
            group.members.append(member)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        questions = [
            QuestionFactory.create(
                letter=letter,
                question_text=f"Question {i}",
                author=UserFactory.create(),
            )
            for i in range(3)
        ] + [
            QuestionFactory.create(
                letter=letter,
                question_text=f"Question 4",
                author=None,
            )
        ]
        db_session.commit()

        db_responses = [
            ResponseFactory.create(
                question=questions[0],
                participant=group.members[0],
            ),
            ResponseFactory.create(
                question=questions[1],
                participant=group.members[1],
            ),
            ResponseFactory.create(
                question=questions[1],
                participant=group.members[2],
            ),
            ResponseFactory.create(
                question=questions[3],
                participant=group.members[3],
            ),
        ]
        db_session.commit()

        letter_dict = letter_crud.compile_letter_dict(letter)
        assert len(letter_dict) == 4
        for question, responses in letter_dict.items():
            assert question in [
                f"{q.author.name}: {q.question_text}"
                if q.author is not None
                else q.question_text
                for q in questions
            ]
            for response, _ in responses:
                assert response in [
                    f"{r.participant.name}: {r.response_text}"
                    for r in db_responses
                ]

    def test_collect_future_letters(self, db_session: Session) -> None:
        curr_time = datetime.now(tz=UTC)
        postpend_letter = LetterFactory.create(
            status=LetterStatus.IN_PROGRESS,
            send_at=curr_time + timedelta(days=6),
        )
        promoted_letter = LetterFactory.create(
            status=LetterStatus.UPCOMING,
            send_at=curr_time + timedelta(days=6),
        )
        g = GroupFactory.create()
        LetterFactory.create(
            group=g,
            status=LetterStatus.IN_PROGRESS,
            send_at=curr_time + timedelta(days=1),
        )
        LetterFactory.create(
            group=g,
            status=LetterStatus.UPCOMING,
            send_at=curr_time + timedelta(days=20),
        )
        LetterFactory.create(
            status=LetterStatus.SENT,
            send_at=curr_time - timedelta(days=3),
        )
        db_session.commit()

        postpend, promote = letter_crud.collect_future_letters(
            db_session, curr_time + timedelta(days=7)
        )
        db_session.commit()

        assert postpend == [postpend_letter]
        assert promote == [promoted_letter]

    def test_collect_future_letters_no_letters(
        self, db_session: Session
    ) -> None:
        curr_time = datetime.now(tz=UTC)
        g = GroupFactory.create()
        LetterFactory.create(
            group=g,
            status=LetterStatus.SENT,
            send_at=curr_time - timedelta(days=3),
        )
        db_session.commit()

        postpend, promote = letter_crud.collect_future_letters(
            db_session, curr_time + timedelta(days=7)
        )
        db_session.commit()

        assert postpend == []
        assert promote == []

    def test_promote_and_create_new_letters(self, db_session: Session) -> None:
        # TODO(#110): Implement celery task testing
        pass

    def test_postpend_upcoming_letters(self, db_session: Session) -> None:
        # TODO(#110): Implement celery task testing
        pass

    def test_add_participants(self, db_session: Session) -> None:
        new_participants = [UserFactory.create() for _ in range(4)]
        letter = LetterFactory.create()
        db_session.commit()

        before_participants = letter.participants
        letter_crud.add_participants(db_session, letter, new_participants)
        db_session.commit()

        assert set(letter.participants) == set(
            before_participants + new_participants
        )
