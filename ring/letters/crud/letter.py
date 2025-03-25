"""CRUD operations for letter management.

This module provides functions for managing letters in the Ring system, including
creation, scheduling, question management, and task scheduling for reminders.
"""

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

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[Letter]: List of letters

    Raises:
        IDNotFoundException: If group with given API ID is not found
    """
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def get_letters_for_user(
    db: Session, user: User, filters: list[ColumnElement[bool]] | None = None
) -> Sequence[Letter]:
    """Return all letters that a user is a participant in.

    Args:
        db (Session): Database session
        user (User): User to get letters for
        filters (list[ColumnElement[bool]] | None, optional): Additional filters to apply. Defaults to None.

    Returns:
        Sequence[Letter]: List of letters
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

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        send_at (datetime): When the letter should be sent
        number (int | None, optional): Sequential number for the letter. Defaults to None.
        letter_status (LetterStatus, optional): Status of the letter. Defaults to UPCOMING.

    Returns:
        Letter: Newly created letter

    Raises:
        IDNotFoundException: If group with given API ID is not found
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

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        send_at (datetime): When the letter should be sent
        number (int | None, optional): Sequential number for the letter. Defaults to None.
        letter_status (LetterStatus, optional): Status of the letter. Defaults to UPCOMING.

    Returns:
        Letter: Newly created letter with questions

    Raises:
        IDNotFoundException: If group with given API ID is not found
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

    Args:
        db (Session): Database session
        letter (Letter): Letter to update
        send_at (datetime): New time to send the letter

    Returns:
        Letter: Updated letter
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

    Args:
        db (Session): Database session
        letter (Letter): Letter to create/update tasks for
        send_at (datetime): When the letter should be sent
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
    """Add a question to a letter.

    Args:
        db (Session): Database session
        letter (Letter): Letter to add question to
        question_text (str): Text of the question
        author (User | None, optional): Author of the question. Defaults to None.

    Returns:
        Question: Created question
    """
    db_question = Question.create(letter, question_text, author=author)
    db.add(db_question)
    return db_question


def add_default_questions(db: Session, letter: Letter) -> Sequence[Question]:
    """Add default questions to a letter.

    Args:
        db (Session): Database session
        letter (Letter): Letter to add questions to

    Returns:
        Sequence[Question]: List of created questions
    """
    questions = []
    for question_text in DEFAULT_QUESTIONS:
        question = add_question(db, letter, question_text)
        questions.append(question)
    return questions


def add_random_questions(
    db: Session, letter: Letter, num_questions: int = 3
) -> Sequence[Question]:
    """Add random questions from the question bank to a letter.

    Args:
        db (Session): Database session
        letter (Letter): Letter to add questions to
        num_questions (int, optional): Number of questions to add. Defaults to 3.

    Returns:
        Sequence[Question]: List of created questions
    """
    questions = []
    for question_text in random.sample(QUESTION_BANK, num_questions):
        question = add_question(db, letter, question_text)
        questions.append(question)
    return questions


def compile_letter_dict(
    letter: Letter,
) -> dict[str, list[tuple[str, list[str]]]]:
    """Compile a letter's questions and responses into a dictionary format.

    Args:
        letter (Letter): Letter to compile

    Returns:
        dict[str, list[tuple[str, list[str]]]]: Dictionary mapping question text to
            list of tuples containing (author name, list of responses)
    """

    def construct_question_text(question: Question) -> str:
        """Construct the display text for a question.

        Args:
            question (Question): Question to format

        Returns:
            str: Formatted question text with optional author
        """
        if question.author:
            return f"{question.question_text} - {question.author.name}"
        return question.question_text

    return {
        construct_question_text(question): [
            (
                response.author.name,
                response.response_text.split("\n"),
            )
            for response in question.responses
        ]
        for question in letter.questions
    }


def collect_future_letters(
    db: Session,
    recent_time: datetime,
) -> tuple[Sequence[Letter], Sequence[Letter]]:
    """Collect letters that need to be promoted or postpended.

    Args:
        db (Session): Database session
        recent_time (datetime): Time threshold for recent letters

    Returns:
        tuple[Sequence[Letter], Sequence[Letter]]: Tuple containing:
            - Letters to be promoted to IN_PROGRESS
            - Letters to be postpended
    """
    letters_to_promote = db.scalars(
        select(Letter).filter(
            Letter.status == LetterStatus.UPCOMING,
            Letter.send_at <= recent_time,
        )
    ).all()

    letters_to_postpend = db.scalars(
        select(Letter).filter(
            Letter.status == LetterStatus.IN_PROGRESS,
            Letter.send_at <= recent_time,
        )
    ).all()

    return letters_to_promote, letters_to_postpend


@register_task_factory(name="promote_and_create_new_letters")
def promote_and_create_new_letters(
    self: CeleryTask, letter_ids: list[int]
) -> None:
    """Promote letters to IN_PROGRESS and create new upcoming letters.

    This task is triggered when letters need to be promoted from UPCOMING to
    IN_PROGRESS status. It also creates new upcoming letters for the affected groups.

    Args:
        self (CeleryTask): Celery task instance
        letter_ids (list[int]): IDs of letters to promote
    """
    letters = self.session.scalars(
        select(Letter).filter(Letter.id.in_(letter_ids))
    ).all()
    for letter in letters:
        letter.status = LetterStatus.IN_PROGRESS
        create_letter_with_questions(
            self.session,
            letter.group.api_identifier,
            letter.send_at + timedelta(days=letter.group.cycle_length),
        )
    self.session.commit()


@register_task_factory(name="postpend_upcoming_letters")
def postpend_upcoming_letters(self: CeleryTask, letter_ids: list[int]) -> None:
    """Move letters to SENT status.

    This task is triggered when letters need to be moved from IN_PROGRESS to
    SENT status.

    Args:
        self (CeleryTask): Celery task instance
        letter_ids (list[int]): IDs of letters to postpend
    """
    letters = self.session.scalars(
        select(Letter).filter(Letter.id.in_(letter_ids))
    ).all()
    for letter in letters:
        letter.status = LetterStatus.SENT
    self.session.commit()


def add_participants(
    db: Session, letter: Letter, participants: list[User]
) -> None:
    """Add participants to a letter.

    Args:
        db (Session): Database session
        letter (Letter): Letter to add participants to
        participants (list[User]): Users to add as participants
    """
    letter.participants.extend(participants)
