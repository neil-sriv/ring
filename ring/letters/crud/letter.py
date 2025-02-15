from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import ColumnElement, select

from ring.api_identifier import util as api_identifier_crud
from ring.letters.constants import (
    DEFAULT_QUESTIONS,
    QUESTION_BANK,
    LetterStatus,
)
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.tasks.crud import schedule as schedule_crud
from ring.tasks.models.task_model import TaskType
from ring.worker.celery_app import register_task_factory

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ring.worker.celery_app import CeleryTask


def get_letters(
    db: Session, group_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Letter]:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def get_letters_for_user(
    db: Session, user: User, filters: list[ColumnElement[bool]] | None = None
) -> Sequence[Letter]:
    """
    Return all letters that a user is a participant in

    :param db: Database session
    :param user: User
    :return: List of letters
    """
    query_filters = [User.id == user.id]
    if filters:
        query_filters.extend(filters)
    return db.scalars(
        select(Letter).join(Letter.participants).filter(*query_filters)
    ).all()


def create_letter(
    db: Session,
    group_api_id: str,
    send_at: datetime,
    number: int | None = None,
    letter_status: LetterStatus = LetterStatus.UPCOMING,
) -> Letter:
    group = api_identifier_crud.get_model(
        db,
        Group,
        api_id=group_api_id,
    )
    db_letter = Letter.create(group, send_at, letter_status, number=number)
    db.add(db_letter)

    if letter_status in [LetterStatus.IN_PROGRESS, LetterStatus.UPCOMING]:
        upsert_letter_tasks(db, db_letter, send_at)
    return db_letter


def create_letter_with_questions(
    db: Session,
    group_api_id: str,
    send_at: datetime,
    number: int | None = None,
    letter_status: LetterStatus = LetterStatus.UPCOMING,
) -> Letter:
    letter = create_letter(db, group_api_id, send_at, number, letter_status)
    add_random_questions(db, letter)
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    if not group.default_questions:
        add_default_questions(db, letter)
    else:
        [
            add_question(db, letter, question.question_text)
            for question in group.default_questions
        ]
    return letter


def edit_letter(
    db: Session,
    letter: Letter,
    send_at: datetime,
) -> Letter:
    upsert_letter_tasks(db, letter, send_at)
    letter.send_at = send_at
    db.flush()
    return letter


def upsert_letter_tasks(
    db: Session, letter: Letter, send_at: datetime
) -> None:
    # send email
    send_email_task = schedule_crud.update_task(
        db,
        letter.group.schedule,
        TaskType.SEND_EMAIL,
        letter.send_at,
        send_at,
    )
    if not send_email_task:
        schedule_crud.register_task(
            db,
            letter.group.schedule,
            TaskType.SEND_EMAIL,
            send_at,
            {},
        )

    # reminder email 1
    if letter.status == LetterStatus.UPCOMING:
        if send_at - timedelta(days=8) < datetime.now(tz=UTC):
            schedule_crud.unregister_task(
                db,
                letter.group.schedule,
                TaskType.REMINDER_EMAIL,
                letter.send_at - timedelta(days=8),
            )
        else:
            reminder_email_task_1 = schedule_crud.update_task(
                db,
                letter.group.schedule,
                TaskType.REMINDER_EMAIL,
                letter.send_at - timedelta(days=8),
                send_at - timedelta(days=8),
            )
            if not reminder_email_task_1:
                schedule_crud.register_task(
                    db,
                    letter.group.schedule,
                    TaskType.REMINDER_EMAIL,
                    send_at - timedelta(days=8),
                    {"letter_status": LetterStatus.UPCOMING},
                )

    # reminder email 2
    if send_at - timedelta(days=1) < datetime.now(tz=UTC):
        schedule_crud.unregister_task(
            db,
            letter.group.schedule,
            TaskType.REMINDER_EMAIL,
            letter.send_at - timedelta(days=1),
        )
    else:
        reminder_email_task_2 = schedule_crud.update_task(
            db,
            letter.group.schedule,
            TaskType.REMINDER_EMAIL,
            letter.send_at - timedelta(days=1),
            send_at - timedelta(days=1),
        )
        if not reminder_email_task_2:
            schedule_crud.register_task(
                db,
                letter.group.schedule,
                TaskType.REMINDER_EMAIL,
                send_at - timedelta(days=1),
                {"letter_status": LetterStatus.IN_PROGRESS},
            )


def add_question(
    db: Session, letter: Letter, question_text: str, author: User | None = None
) -> Question:
    question = Question.create(letter, question_text, author)
    db.add(question)
    letter.questions.append(question)
    return question


def add_default_questions(db: Session, letter: Letter) -> Sequence[Question]:
    questions = [
        Question.create(
            letter,
            text,
            author=None,
        )
        for text in DEFAULT_QUESTIONS
    ]
    db.add_all(questions)
    letter.questions.extend(questions)
    return questions


def add_random_questions(
    db: Session, letter: Letter, num_questions: int = 3
) -> Sequence[Question]:
    questions: list[Question] = []
    texts = random.sample(QUESTION_BANK, num_questions)
    for text in texts:
        # idx = randint(0, len(DEFAULT_QUESTIONS) - 1)
        question = Question.create(
            letter,
            text,
            author=None,
        )
        questions.append(question)
    db.add_all(questions)
    letter.questions.extend(questions)
    return questions


def compile_letter_dict(
    letter: Letter,
) -> dict[str, list[tuple[str, list[str]]]]:
    def construct_question_text(question: Question) -> str:
        return (
            f"{question.author.name}: {question.question_text}"
            if question.author
            else question.question_text
        )

    return {
        construct_question_text(q): [
            (
                f"{resp.participant.name}: {resp.response_text}",
                [
                    assoc.image.qualified_s3_url
                    for assoc in resp.image_associations
                ],
            )
            for resp in q.responses
        ]
        for q in sorted(
            letter.questions, key=lambda q: q.created_at, reverse=True
        )
    }


def collect_future_letters(
    db: Session,
    recent_time: datetime,
) -> tuple[Sequence[Letter], Sequence[Letter]]:
    letters = db.scalars(
        select(Letter)
        .where(
            Letter.send_at < recent_time,
            Letter.status.in_(
                [LetterStatus.IN_PROGRESS, LetterStatus.UPCOMING]
            ),
        )
        .order_by(Letter.send_at)
    ).all()
    letters_to_be_postpended: list[Letter] = []
    letters_to_be_promoted: list[Letter] = []
    for letter in letters:
        if letter.status == LetterStatus.IN_PROGRESS:
            if not letter.group.upcoming_letter:
                letters_to_be_postpended.append(letter)
        else:
            if not letter.group.in_progress_letter:
                letters_to_be_promoted.append(letter)

    return letters_to_be_postpended, letters_to_be_promoted


@register_task_factory(name="promote_and_create_new_letters")
def promote_and_create_new_letters(
    self: CeleryTask, letter_ids: list[int]
) -> None:
    letters = (
        self.session.query(Letter).filter(Letter.id.in_(letter_ids)).all()
    )
    for letter in letters:
        letter.status = LetterStatus.IN_PROGRESS
        create_letter_with_questions(
            self.session,
            letter.group.api_identifier,
            letter.send_at + timedelta(days=30),
        )
    self.session.commit()


@register_task_factory(name="postpend_upcoming_letters")
def postpend_upcoming_letters(self: CeleryTask, letter_ids: list[int]) -> None:
    letters = (
        self.session.query(Letter).filter(Letter.id.in_(letter_ids)).all()
    )
    for letter in letters:
        create_letter_with_questions(
            self.session,
            letter.group.api_identifier,
            letter.send_at + timedelta(days=30),
        )
    self.session.commit()


def add_participants(
    db: Session, letter: Letter, participants: list[User]
) -> None:
    for participant in participants:
        letter.participants.append(participant)
