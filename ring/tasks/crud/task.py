"""CRUD operations and task execution handlers for Ring's task system.

This module provides functions for executing different types of tasks in Ring,
particularly focusing on email-related tasks like sending letters and reminders.
It includes both synchronous execution functions and their asynchronous job wrappers.
"""

from __future__ import annotations

import math
from datetime import timedelta
from numbers import Real
from typing import Any, Callable

import sqlalchemy
from loguru import logger
from sqlalchemy.orm import Session

from ring.async_scheduler.scheduler import job_factory, scheduler
from ring.email_util import send_email
from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.lib.util import RegistrationDict
from ring.tasks.crud.reminder_email_task import construct_reminder_email
from ring.tasks.crud.response_open_email_task import (
    construct_response_open_email,
)
from ring.tasks.crud.send_email_task import construct_send_letter_email
from ring.tasks.models.task_model import (
    ReminderEmailTask,
    SendEmailTask,
    Task,
    TaskStatus,
    TaskType,
)

GROUP_SETTING_MIN_RESPONDERS_KEY = "letter_send_min_responders"
GROUP_SETTING_MIN_RESPONDER_RATIO_KEY = "letter_send_min_responder_ratio"
DEFAULT_MIN_RESPONDER_RATIO_TO_SEND = 0.5
LETTER_SEND_DEFERRAL_DAYS = 1


def _parse_positive_int(value: Any) -> int | None:
    """Parse a value into a positive integer, returning None if invalid."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        if value.is_integer() and value > 0:
            return int(value)
        return None
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        if parsed.is_integer() and parsed > 0:
            return int(parsed)
    return None


def _parse_ratio(value: Any) -> float | None:
    """Parse a value into a ratio in the (0, 1] range."""
    if isinstance(value, bool) or not isinstance(value, Real):
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                return None
        else:
            return None
    ratio = float(value)
    if ratio <= 0 or ratio > 1:
        return None
    return ratio


def _minimum_responders_required(letter: Letter) -> int:
    """Return the minimum unique responder count required to send.

    Group-level configuration (stored in group key-values):
    - `letter_send_min_responders`: positive integer responder count
    - `letter_send_min_responder_ratio`: ratio in (0, 1]
    """
    participant_count = len(letter.participants)
    if participant_count <= 0:
        return 0

    min_responders_setting = letter.group.key_values.get_value(
        GROUP_SETTING_MIN_RESPONDERS_KEY
    )
    configured_min_responders = _parse_positive_int(min_responders_setting)
    if configured_min_responders is not None:
        return min(participant_count, configured_min_responders)

    ratio_setting = letter.group.key_values.get_value(
        GROUP_SETTING_MIN_RESPONDER_RATIO_KEY
    )
    configured_ratio = _parse_ratio(ratio_setting)
    ratio = (
        configured_ratio
        if configured_ratio is not None
        else DEFAULT_MIN_RESPONDER_RATIO_TO_SEND
    )
    return max(1, math.ceil(participant_count * ratio))


def execute_reminder_email_task(
    db: Session,
    task: ReminderEmailTask,
    letter_status: LetterStatus = LetterStatus.UPCOMING,
    **kwargs: Any,
) -> None:
    """Execute a reminder email task.

    Sends a reminder email to participants about an upcoming or in-progress letter.
    The timing of the reminder depends on the letter's status:
    - For upcoming letters: 8 days before send date
    - For in-progress letters: 1 day before send date

    Args:
        db: Database session
        task: The reminder email task to execute
        letter_status: Status of the letter to send reminder for (default: UPCOMING)

    Raises:
        AssertionError: If letter timing doesn't match task execution time
    """
    group = task.schedule.group
    if letter_id := kwargs.get("letter_id"):
        letter_to_send = db.scalars(
            sqlalchemy.select(Letter).where(Letter.id == letter_id)
        ).one()
    else:
        letter_to_send = (
            group.in_progress_letters[0]
            if letter_status == LetterStatus.IN_PROGRESS
            else group.upcoming_letters[0]
        )
    assert letter_to_send
    if letter_to_send.status == LetterStatus.UPCOMING:
        assert task.execute_at == letter_to_send.send_at - timedelta(days=8)
    if letter_to_send.status == LetterStatus.IN_PROGRESS:
        assert task.execute_at == letter_to_send.send_at - timedelta(days=1)
    message_id = send_email(
        construct_reminder_email(
            [u.email for u in letter_to_send.participants],
            group.name,
            letter_to_send.api_identifier,
            letter_to_send.status,
        )
    )
    if message_id:
        logger.info("Message ID:" + message_id)
        logger.info(
            "Sent reminder email to {}".format(
                [u.email for u in letter_to_send.participants]
            )
        )

    db.commit()


def execute_send_email_task(
    db: Session, task: SendEmailTask, **kwargs: Any
) -> None:
    """Execute a send email task.

    Sends a letter email to all participants and marks the letter as sent
    upon successful delivery.

    Args:
        db: Database session
        task: The send email task to execute
        **kwargs: Additional arguments for the task
    Raises:
        AssertionError: If no in-progress letter is found
    """
    logger.debug(f"Executing send email task with kwargs: {kwargs}")
    letter_id = kwargs.get("letter_id")
    if letter_id:
        letter = db.scalars(
            sqlalchemy.select(Letter).where(Letter.id == letter_id)
        ).one()
        assert letter
        letter_to_send = letter
    else:
        group = task.schedule.group
        letter_to_send = group.in_progress_letters[0]
    assert letter_to_send

    if letter_to_send.status == LetterStatus.IN_PROGRESS:
        required_responders = _minimum_responders_required(letter_to_send)
        responder_count = len(letter_to_send.responders)
        if responder_count < required_responders:
            new_send_at = letter_to_send.send_at + timedelta(
                days=LETTER_SEND_DEFERRAL_DAYS
            )
            logger.info(
                "Deferring letter {} send from {} to {}: responders {}/{}".format(
                    letter_to_send.id,
                    letter_to_send.send_at,
                    new_send_at,
                    responder_count,
                    required_responders,
                )
            )
            letter_crud.edit_letter(db, letter_to_send, send_at=new_send_at)
            db.commit()
            return

    title = f"Ring Newsletter {("#" + str(letter_to_send.number)) if not letter_to_send.title else str(letter_to_send.title)} for {letter_to_send.group.name}"
    message_id = send_email(
        construct_send_letter_email(
            [u.email for u in letter_to_send.participants],
            title,
            letter_to_send.api_identifier,
            letter_crud.compile_letter_dict(letter_to_send),
        )
    )
    if message_id:
        letter_to_send.status = LetterStatus.SENT
        logger.info("Message ID:" + message_id)
        logger.info(
            "Sent letter email to {}".format(
                [u.email for u in letter_to_send.participants]
            )
        )

    db.commit()


def _find_and_execute_task(
    db: Session,
    task_id: int,
    task_class: type[Task],
    execute_fn: Callable[[Session, Task], None],
    **kwargs: Any,
) -> Task:
    """Find and execute a task with error handling.

    Args:
        db: Database session
        task_id: ID of the task to execute
        task_class: Class of the task (e.g., SendEmailTask)
        execute_fn: Function to execute the task
        **kwargs: Additional arguments for the execute function

    Returns:
        Task: The executed task

    Raises:
        Exception: Any error that occurred during task execution
    """
    task = db.query(task_class).filter(task_class.id == task_id).one()
    try:
        execute_fn(db, task, **kwargs)
    except Exception as e:
        db.rollback()
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        logger.info("Failed to execute task {}: {}".format(task_id, e))
        raise e
    else:
        task.message = ""
        task.status = TaskStatus.COMPLETED
        logger.info("Task {} executed successfully".format(task_id))
    return task


@job_factory("send_email_task")
def async_send_email_task(db: Session, task_id: int, **kwargs: Any) -> None:
    """Job for executing send email tasks asynchronously.

    Args:
        db: Database session
        task_id: ID of the task to execute
        **kwargs: Additional arguments for the execute function
    """
    _find_and_execute_task(
        db, task_id, SendEmailTask, execute_send_email_task, **kwargs
    )
    db.commit()


@job_factory("reminder_email_task")
def async_reminder_email_task(
    db: Session, task_id: int, **kwargs: Any
) -> None:
    """Job for executing reminder email tasks asynchronously.

    Args:
        db: Database session
        task_id: ID of the task to execute
        **kwargs: Additional arguments for the execute function
    """
    _find_and_execute_task(
        db,
        task_id,
        ReminderEmailTask,
        execute_reminder_email_task,
        **kwargs,
    )
    db.commit()


ASYNC_TASK_TO_EXECUTE_MAPPING: dict[
    TaskType, Callable[[Session, int], None]
] = {
    TaskType.SEND_EMAIL: async_send_email_task,
    TaskType.REMINDER_EMAIL: async_reminder_email_task,
}


@job_factory("send_response_open_email")
def send_response_open_email(db: Session, letter_id: int) -> None:
    """Send an email notifying participants that a newsletter is open for responses.

    This job is triggered when a letter is promoted from UPCOMING to IN_PROGRESS
    status. It sends an email to all participants letting them know they can now
    add their responses.

    Args:
        db: Database session
        letter_id: ID of the letter that was promoted
    """
    letter = db.scalars(
        sqlalchemy.select(Letter).where(Letter.id == letter_id)
    ).one()

    letter_title = f"#{letter.number}" if not letter.title else letter.title
    recipients = [u.email for u in letter.participants]

    if not recipients:
        logger.info(
            f"No recipients for response open email for letter {letter_id}"
        )
        return

    email_draft = construct_response_open_email(
        recipients,
        letter.group.name,
        letter.api_identifier,
        letter_title,
    )
    message_id = send_email(email_draft)
    if message_id:
        logger.info(
            f"Sent response open email for letter {letter_id} to {recipients}"
        )


# TASK_REGISTRY: RegistrationDict[TaskType, Callable[[Any], None]] = (
#     RegistrationDict("TASK_REGISTRY")
# )


@job_factory("execute_tasks")
def execute_tasks_async(db: Session, task_ids: list[int]) -> None:
    """Execute a list of tasks asynchronously.

    Args:
        db: Database session
        task_ids: List of task IDs to execute
    """
    execute_tasks(db, task_ids)
    db.commit()


def execute_tasks(db: Session, task_ids: list[int]) -> None:
    """Execute a list of tasks synchronously.

    Args:
        db: Database session
        task_ids: List of task IDs to execute

    Raises:
        Exception: Any error that occurred during task execution
    """
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    for task in tasks:
        task.status = TaskStatus.IN_PROGRESS
    db.flush()
    for task in tasks:
        task_type = TaskType(task.type)
        task_to_execute = ASYNC_TASK_TO_EXECUTE_MAPPING[task_type]
        scheduler.add_job(
            task_to_execute,
            args=[task.id],
            kwargs=task.arguments,
        )
