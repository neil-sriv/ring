"""CRUD operations and task execution handlers for Ring's task system.

This module provides functions for executing different types of tasks in Ring,
particularly focusing on email-related tasks like sending letters and reminders.
It includes both synchronous execution functions and their asynchronous job wrappers.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

import sqlalchemy
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ring.async_scheduler.scheduler import job_factory, scheduler
from ring.email_util import send_email
from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.letters.send_threshold import defer_letter_send_if_below_threshold
from ring.lib.util import RegistrationDict
from ring.tasks.crud.reminder_email_task import construct_reminder_email
from ring.tasks.crud.response_open_email_task import (
    construct_response_open_email,
)
from ring.tasks.crud.waiting_response_email_task import (
    construct_waiting_response_email,
    letter_display_title,
    letter_non_responder_emails,
)
from ring.tasks.models.task_model import (
    ReminderEmailTask,
    SendEmailTask,
    Task,
    TaskStatus,
    TaskType,
)


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
    upon successful delivery. If the group has no upcoming letter after a
    successful send (normally created when the letter was promoted), the
    next letter is created here so the group's cadence continues.

    Args:
        db: Database session
        task: The send email task to execute
        **kwargs: Additional arguments for the task
    """
    logger.debug(f"Executing send email task with kwargs: {kwargs}")
    letter_id = kwargs.get("letter_id")
    if letter_id:
        letter_to_send = db.scalars(
            sqlalchemy.select(Letter).where(Letter.id == letter_id)
        ).one()
    else:
        # Legacy tasks were registered before the letter was flushed, so
        # their arguments hold "letter_id": None and the letter has to be
        # inferred from the group's current in-progress letter.
        group = task.schedule.group
        if not group.in_progress_letters:
            logger.info(
                "Send email task {} has no letter to send: group {} has "
                "no in-progress letter".format(task.id, group.id)
            )
            db.commit()
            return
        letter_to_send = group.in_progress_letters[0]

    if letter_to_send.status == LetterStatus.SENT:
        logger.info(
            "Letter {} is already sent; skipping send email task {}".format(
                letter_to_send.id, task.id
            )
        )
        db.commit()
        return

    if defer_letter_send_if_below_threshold(db, letter_to_send):
        db.commit()
        return

    if (
        letter_crud.send_letter_email(db, letter_to_send)
        and not letter_to_send.group.upcoming_letters
    ):
        letter_crud.create_letter_with_questions(
            db,
            letter_to_send.group.api_identifier,
            letter_to_send.send_at
            + timedelta(days=letter_to_send.group.cycle_length),
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
    except OperationalError as e:
        # Transient database errors (e.g. CockroachDB serialization
        # failures) must not kill the task for good: put it back in
        # PENDING so the next scheduler poll retries it.
        db.rollback()
        task.status = TaskStatus.PENDING
        task.message = f"retrying after transient database error: {e}"
        db.commit()
        logger.info(
            "Task {} hit a transient database error and will be "
            "retried: {}".format(task_id, e)
        )
        raise e
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


def requeue_in_progress_tasks(db: Session) -> int:
    """Reset tasks stranded IN_PROGRESS back to PENDING.

    Called at app startup, right after the APScheduler jobstore has been
    wiped: any task still IN_PROGRESS at that point was claimed by a poll
    cycle whose jobs died with the previous process (restart or deploy),
    so nothing will ever execute or repair it. Without this, the letter
    behind a stranded send task is frozen: the task is never re-collected
    (only PENDING tasks are), and the postpend job skips the letter
    because a send task still appears responsible for it.

    Returns:
        int: Number of tasks put back in PENDING.
    """
    stranded = db.scalars(
        sqlalchemy.select(Task).where(
            Task.status == TaskStatus.IN_PROGRESS,
        )
    ).all()
    for task in stranded:
        task.status = TaskStatus.PENDING
        task.message = (
            "requeued at startup: task was in progress when the previous "
            "process stopped"
        )
        logger.info(
            "Requeueing task {} ({}) stranded in progress at {}".format(
                task.id, task.type, task.execute_at
            )
        )
    db.commit()
    return len(stranded)


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


@job_factory("send_waiting_response_email")
def send_waiting_response_email(db: Session, letter_id: int) -> None:
    """Email participants who have not yet answered a deferred letter.

    Triggered once when a letter send is deferred because too few people
    have responded. Recipients are letter participants minus responders.
    No-ops if that list is empty.

    Args:
        db: Database session
        letter_id: ID of the deferred letter
    """
    letter = db.scalars(
        sqlalchemy.select(Letter).where(Letter.id == letter_id)
    ).one()

    recipients = letter_non_responder_emails(letter)
    if not recipients:
        logger.info(
            f"No non-responders for waiting-response email for letter {letter_id}"
        )
        return

    email_draft = construct_waiting_response_email(
        recipients,
        letter.group.name,
        letter.api_identifier,
        letter_display_title(letter),
    )
    message_id = send_email(email_draft)
    if message_id:
        logger.info(
            "Sent waiting-response email for letter {} to {}".format(
                letter_id, recipients
            )
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

    Tasks without a registered executor (unknown or retired task types)
    are marked FAILED instead of aborting the whole batch, so one bad row
    in the task table can never block every other scheduled send.

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
        try:
            task_to_execute = ASYNC_TASK_TO_EXECUTE_MAPPING[
                TaskType(task.type)
            ]
        except (KeyError, ValueError):
            task.status = TaskStatus.FAILED
            task.message = "no executor registered for task type {!r}".format(
                task.type
            )
            logger.warning(
                "Skipping task {}: no executor for task type {!r}".format(
                    task.id, task.type
                )
            )
            continue
        scheduler.add_job(
            task_to_execute,
            args=[task.id],
            kwargs=task.arguments,
        )
