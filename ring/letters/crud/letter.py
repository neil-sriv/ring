"""CRUD operations for letter management.

This module provides functions for managing letters in the Ring system, including
creation, scheduling, question management, and task scheduling for reminders.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Sequence

from loguru import logger
from sqlalchemy import ColumnElement, select

from ring.api_identifier import util as api_identifier_crud
from ring.async_scheduler.scheduler import job_factory
from ring.letters.constants import (
    DEFAULT_QUESTIONS,
    QUESTION_BANK,
    LetterStatus,
    LetterType,
)
from ring.letters.crud.question import create_question
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.search.crud.hybrid_search import (
    create_hybrid_search_document,
    register_search_function,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    SearchableType,
)
from ring.tasks.crud import schedule as schedule_crud
from ring.tasks.models.task_model import Task, TaskType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_letters(
    db: Session,
    group_api_id: str,
    letter_type: LetterType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Letter]:
    """Retrieve letters for a specific group with pagination.

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        letter_type (LetterType): Type of letter to get
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[Letter]: List of letters

    Raises:
        IDNotFoundException: If group with given API ID is not found
    """
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    query = select(Letter).filter(Letter.group == group)
    if letter_type:
        query = query.filter(Letter.letter_type == letter_type)
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()


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
    letter_type: LetterType = LetterType.CYCLIC,
    title: str | None = None,
) -> Letter:
    """Create a new letter for a group.

    Args:
        db (Session): Database session
        group_api_id (str): API identifier of the group
        send_at (datetime): When the letter should be sent
        number (int | None, optional): Sequential number for the letter. Defaults to None.
        letter_status (LetterStatus, optional): Status of the letter. Defaults to UPCOMING.
        letter_type (LetterType, optional): Type of letter. Defaults to CYCLIC.
        title (str | None, optional): Title of the letter. Defaults to None.

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
    db_letter = Letter.create(
        group,
        send_at,
        letter_status,
        number=number,
        letter_type=letter_type,
        title=title,
    )
    db.add(db_letter)
    if search_document := create_letter_search_document(db, db_letter):
        db.add(search_document)

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
    send_at: datetime | None = None,
    title: str | None = None,
    status: LetterStatus | None = None,
) -> Letter:
    """Update a letter's send time and associated tasks.

    Args:
        db (Session): Database session
        letter (Letter): Letter to update
        send_at (datetime): New time to send the letter

    Returns:
        Letter: Updated letter
    """
    if send_at:
        upsert_letter_tasks(db, letter, send_at)
        letter.send_at = send_at
    if status:
        letter.status = status
        if status == LetterStatus.IN_PROGRESS:
            delete_letter_task(
                db,
                letter,
                TaskType.REMINDER_EMAIL,
                LetterStatus.UPCOMING,
                letter.id,
            )
    if title:
        letter.title = title
    db.flush()
    return letter


def delete_letter_task(
    db: Session,
    letter: Letter,
    task_type: TaskType,
    letter_status: LetterStatus,
    letter_id: int,
) -> None:
    """Delete a letter task.

    Args:
        db (Session): Database session
        letter (Letter): Letter to delete task for
        task_type (TaskType): Type of task to delete
    """
    schedule_crud.unregister_task(
        db,
        letter.group.schedule,
        task_type,
        filters=[
            Task.arguments
            == {"letter_id": letter_id, "letter_status": letter_status},
        ],
    )


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
        {"letter_id": letter.id},
    )
    if not send_email_task:
        schedule_crud.register_task(
            db,
            letter.group.schedule,
            TaskType.SEND_EMAIL,
            send_at,
            {"letter_id": letter.id},
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
                    {
                        "letter_id": letter.id,
                        "letter_status": LetterStatus.UPCOMING,
                    },
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
                {
                    "letter_id": letter.id,
                    "letter_status": LetterStatus.IN_PROGRESS,
                },
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
    return create_question(db, letter, question_text, author=author)


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
        return (
            f"{question.author.name}: {question.question_text}"
            if question.author
            else question.question_text
        )

    return {
        construct_question_text(question): [
            (
                f"{response.participant.name}: {response.response_text}",
                [
                    assoc.image.qualified_s3_url
                    for assoc in response.image_associations
                ],
            )
            for response in question.responses
        ]
        for question in sorted(
            letter.questions, key=lambda q: q.created_at, reverse=True
        )
    }


def collect_future_letters(
    db: Session,
    recent_time: datetime,
) -> tuple[Sequence[Letter], Sequence[Letter]]:
    """Collect letters that need to be promoted or postpended.

    This function collects letters that need to be promoted or postpended based on
    the time threshold for recent letters and only if the group does not already
    have a letter in the same status.

    Args:
        db (Session): Database session
        recent_time (datetime): Time threshold for recent letters

    Returns:
        tuple[Sequence[Letter], Sequence[Letter]]: Tuple containing:
            - Letters to be postpended
            - Letters to be promoted to IN_PROGRESS
    """
    letters_to_promote = db.scalars(
        select(Letter)
        .where(
            Letter.letter_type == LetterType.CYCLIC,
            Letter.status == LetterStatus.UPCOMING,
            Letter.send_at <= recent_time,
        )
        .order_by(Letter.send_at)
    ).all()

    letters_to_postpend = db.scalars(
        select(Letter)
        .where(
            Letter.letter_type == LetterType.CYCLIC,
            Letter.status == LetterStatus.IN_PROGRESS,
            Letter.send_at <= recent_time,
        )
        .order_by(Letter.send_at)
    ).all()
    letters_to_promote = [
        l for l in letters_to_promote if not l.group.in_progress_letters
    ]
    letters_to_postpend = [
        l for l in letters_to_postpend if not l.group.upcoming_letters
    ]
    return letters_to_postpend, letters_to_promote


@job_factory("promote_and_create_new_letters")
def promote_and_create_new_letters(db: Session, letter_ids: list[int]) -> None:
    """Promote letters to IN_PROGRESS and create new upcoming letters.

    This task is triggered when letters need to be promoted from UPCOMING to
    IN_PROGRESS status. It also creates new upcoming letters for the affected groups
    and sends email notifications to participants that the newsletter is now open
    for responses.

    Args:
        db (Session): Database session
        letter_ids (list[int]): IDs of letters to promote
    """
    from ring.email_util import send_email
    from ring.tasks.crud.response_open_email_task import (
        construct_response_open_email,
    )

    logger.info(f"Promoting letters: {letter_ids}")
    letters = db.scalars(select(Letter).where(Letter.id.in_(letter_ids))).all()
    for letter in letters:
        letter.status = LetterStatus.IN_PROGRESS
        create_letter_with_questions(
            db,
            letter.group.api_identifier,
            letter.send_at + timedelta(days=letter.group.cycle_length),
        )
        # Send email notification that the newsletter is now open for responses
        letter_title = (
            f"#{letter.number}"
            if not letter.title
            else letter.title
        )
        recipients = [u.email for u in letter.participants]
        if recipients:
            email_draft = construct_response_open_email(
                recipients,
                letter.group.name,
                letter.api_identifier,
                letter_title,
            )
            message_id = send_email(email_draft)
            if message_id:
                logger.info(
                    f"Sent response open email for letter {letter.id} "
                    f"to {recipients}"
                )
    db.commit()


@job_factory("postpend_upcoming_letters")
def postpend_upcoming_letters(db: Session, letter_ids: list[int]) -> None:
    """Move letters to SENT status.

    This task is triggered when letters need to be moved from IN_PROGRESS to
    SENT status. It also creates a new upcoming letter for the affected groups.

    Args:
        db (Session): Database session
        letter_ids (list[int]): IDs of letters to postpend
    """
    letters = db.scalars(select(Letter).where(Letter.id.in_(letter_ids))).all()
    for letter in letters:
        letter.status = LetterStatus.SENT
        create_letter_with_questions(
            db,
            letter.group.api_identifier,
            letter.send_at + timedelta(days=letter.group.cycle_length),
        )
    db.commit()


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


@register_search_function(SearchableType.LETTER, Letter)
def create_letter_search_document(
    db: Session, letter: Letter
) -> HybridSearchDocument:
    """Create a search document for a letter.

    Args:
        db (Session): Database session
        letter (Letter): Letter to create a search document for

    Returns:
        HybridSearchDocument: Search document for the letter
    """
    question_texts = " ".join(
        question.question_text for question in letter.questions
    )
    participant_names = " ".join(
        participant.name for participant in letter.participants
    )
    raw_text = f"{letter.group.name} {question_texts} {participant_names}"
    return create_hybrid_search_document(
        db, raw_text, letter.api_identifier, SearchableType.LETTER
    )
