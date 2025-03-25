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
    """Retrieve letters for a specific group with pagination.

    :param db: Database session
    :param group_api_id: API identifier of the group
    :param skip: Number of records to skip, defaults to 0
    :param limit: Maximum number of records to return, defaults to 100
    :return: Sequence of letters
    :rtype: Sequence[Letter]
    :raises IDNotFoundException: If group with given API ID is not found
    """
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def get_letters_for_user(
    db: Session, user: User, filters: list[ColumnElement[bool]] | None = None
) -> Sequence[Letter]:
    """Return all letters that a user is a participant in.

    :param db: Database session
    :param user: User to get letters for
    :param filters: Additional filters to apply to the query, defaults to None
    :return: Sequence of letters
    :rtype: Sequence[Letter]
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
    """Create a new letter for a group.

    :param db: Database session
    :param group_api_id: API identifier of the group
    :param send_at: When the letter should be sent
    :param number: Optional sequential number for the letter
    :param letter_status: Status of the letter, defaults to UPCOMING
    :return: Newly created letter
    :rtype: Letter
    :raises IDNotFoundException: If group with given API ID is not found
    """
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
    """Create a new letter with default and random questions.

    :param db: Database session
    :param group_api_id: API identifier of the group
    :param send_at: When the letter should be sent
    :param number: Optional sequential number for the letter
    :param letter_status: Status of the letter, defaults to UPCOMING
    :return: Newly created letter with questions
    :rtype: Letter
    :raises IDNotFoundException: If group with given API ID is not found
    """
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
    """Update a letter's send time and associated tasks.

    :param db: Database session
    :param letter: Letter to update
    :param send_at: New time to send the letter
    :return: Updated letter
    :rtype: Letter
    """
    upsert_letter_tasks(db, letter, send_at)
    letter.send_at = send_at
    db.flush()
    return letter


def upsert_letter_tasks(
    db: Session, letter: Letter, send_at: datetime
) -> None:
    """Create or update tasks associated with a letter.

    Creates or updates tasks for:
    - Sending the letter email
    - Sending reminder emails (8 days and 1 day before)

    :param db: Database session
    :param letter: Letter to create/update tasks for
    :param send_at: When the letter should be sent
    """
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
    """Add a new question to a letter.

    :param db: Database session
    :param letter: Letter to add the question to
    :param question_text: Text content of the question
    :param author: Optional author of the question
    :return: Newly created question
    :rtype: Question
    """
    question = Question.create(letter, question_text, author)
    db.add(question)
    letter.questions.append(question)
    return question


def add_default_questions(db: Session, letter: Letter) -> Sequence[Question]:
    """Add the standard set of default questions to a letter.

    :param db: Database session
    :param letter: Letter to add default questions to
    :return: Sequence of created questions
    :rtype: Sequence[Question]
    """
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
    """Add random questions from the question bank to a letter.

    :param db: Database session
    :param letter: Letter to add questions to
    :param num_questions: Number of random questions to add, defaults to 3
    :return: Sequence of created questions
    :rtype: Sequence[Question]
    """
    questions = random.sample(QUESTION_BANK, num_questions)
    db_questions = [
        Question.create(
            letter,
            text,
            author=None,
        )
        for text in questions
    ]
    db.add_all(db_questions)
    letter.questions.extend(db_questions)
    return db_questions


def compile_letter_dict(
    letter: Letter,
) -> dict[str, list[tuple[str, list[str]]]]:
    """Compile a letter's questions and responses into a dictionary format.

    :param letter: Letter to compile
    :return: Dictionary containing questions and responses
    :rtype: dict[str, list[tuple[str, list[str]]]]
    """
    def construct_question_text(question: Question) -> str:
        """Construct the display text for a question.

        :param question: Question to construct text for
        :return: Formatted question text
        :rtype: str
        """
        return (
            f"{question.question_text} (by {question.author.name})"
            if question.author
            else question.question_text
        )

    return {
        "questions": [
            (
                construct_question_text(question),
                [response.response_text for response in question.responses],
            )
            for question in letter.questions
        ]
    }


def collect_future_letters(
    db: Session,
    recent_time: datetime,
) -> tuple[Sequence[Letter], Sequence[Letter]]:
    """Collect letters that need to be processed for status updates.

    :param db: Database session
    :param recent_time: Time threshold for recent letters
    :return: Tuple of (letters to promote, letters to postpend)
    :rtype: tuple[Sequence[Letter], Sequence[Letter]]
    """
    letters_to_promote = db.scalars(
        select(Letter)
        .filter(
            Letter.status == LetterStatus.UPCOMING,
            Letter.send_at <= recent_time,
        )
        .order_by(Letter.send_at)
    ).all()

    letters_to_postpend = db.scalars(
        select(Letter)
        .filter(
            Letter.status == LetterStatus.IN_PROGRESS,
            Letter.send_at <= recent_time,
        )
        .order_by(Letter.send_at)
    ).all()

    return letters_to_promote, letters_to_postpend


@register_task_factory(name="promote_and_create_new_letters")
def promote_and_create_new_letters(
    self: CeleryTask, letter_ids: list[int]
) -> None:
    """Promote upcoming letters to in-progress and create new upcoming letters.

    :param self: Celery task instance
    :param letter_ids: IDs of letters to promote
    """
    with self.session() as db:
        for letter_id in letter_ids:
            letter = db.get(Letter, letter_id)
            if not letter:
                continue
            letter.status = LetterStatus.IN_PROGRESS
            create_letter_with_questions(
                db,
                letter.group.api_identifier,
                letter.send_at + timedelta(days=14),
            )
        db.commit()


@register_task_factory(name="postpend_upcoming_letters")
def postpend_upcoming_letters(self: CeleryTask, letter_ids: list[int]) -> None:
    """Mark in-progress letters as sent and adjust upcoming letters.

    :param self: Celery task instance
    :param letter_ids: IDs of letters to process
    """
    with self.session() as db:
        for letter_id in letter_ids:
            letter = db.get(Letter, letter_id)
            if not letter:
                continue
            letter.status = LetterStatus.SENT
        db.commit()


def add_participants(
    db: Session, letter: Letter, participants: list[User]
) -> None:
    """Add participants to a letter.

    :param db: Database session
    :param letter: Letter to add participants to
    :param participants: List of users to add as participants
    """
    letter.participants.extend(participants)
    db.flush()
