"""CRUD operations and task execution handlers for Ring's task system.

This module provides functions for executing different types of tasks in Ring,
particularly focusing on email-related tasks like sending letters and reminders.
It includes both synchronous execution functions and their asynchronous Celery
task wrappers.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

from sqlalchemy.orm import Session

from ring.email_util import send_email
from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.tasks.crud.reminder_email_task import construct_reminder_email
from ring.tasks.crud.send_email_task import construct_send_letter_email
from ring.tasks.models.task_model import (
    ReminderEmailTask,
    SendEmailTask,
    Task,
    TaskStatus,
    TaskType,
)
from ring.worker.celery_app import (  # type: ignore
    CeleryTask,
    register_task_factory,
)


def execute_reminder_email_task(
    db: Session,
    task: ReminderEmailTask,
    letter_status: LetterStatus = LetterStatus.UPCOMING,
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
    letter_to_send = (
        group.in_progress_letter
        if letter_status == LetterStatus.IN_PROGRESS
        else group.upcoming_letter
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
        print("Message ID:", message_id)
        print(
            "Sent reminder email to %s",
            [u.email for u in letter_to_send.participants],
        )

    db.commit()


def execute_send_email_task(db: Session, task: SendEmailTask) -> None:
    """Execute a send email task.

    Sends a letter email to all participants and marks the letter as sent
    upon successful delivery.

    Args:
        db: Database session
        task: The send email task to execute

    Raises:
        AssertionError: If no in-progress letter is found
    """
    group = task.schedule.group
    letter_to_send = group.in_progress_letter
    assert letter_to_send
    message_id = send_email(
        construct_send_letter_email(
            [u.email for u in letter_to_send.participants],
            letter_to_send.number,
            group.name,
            letter_to_send.api_identifier,
            letter_crud.compile_letter_dict(letter_to_send),
        )
    )
    if message_id:
        letter_to_send.status = LetterStatus.SENT
        print("Message ID:", message_id)
        print(
            "Sent letter email to %s",
            [u.email for u in letter_to_send.participants],
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
        db.commit()
        task.message = str(e)
        print(f"Failed to execute task {task_id}: {e}")
        raise e
    else:
        task.message = ""
        task.status = TaskStatus.COMPLETED
        print(f"Task {task_id} executed successfully")
    return task


@register_task_factory(name="send_email_task")
def async_send_email_task(
    self: CeleryTask, task_id: int, **kwargs: Any
) -> None:
    """Celery task for executing send email tasks asynchronously.

    Args:
        self: Celery task instance
        task_id: ID of the task to execute
        **kwargs: Additional arguments for the execute function
    """
    _find_and_execute_task(
        self.session, task_id, SendEmailTask, execute_send_email_task, **kwargs
    )
    self.session.commit()


@register_task_factory(name="reminder_email_task")
def async_reminder_email_task(
    self: CeleryTask, task_id: int, **kwargs: Any
) -> None:
    """Celery task for executing reminder email tasks asynchronously.

    Args:
        self: Celery task instance
        task_id: ID of the task to execute
        **kwargs: Additional arguments for the execute function
    """
    _find_and_execute_task(
        self.session,
        task_id,
        ReminderEmailTask,
        execute_reminder_email_task,
        **kwargs,
    )
    self.session.commit()


ASYNC_TASK_TO_EXECUTE_MAPPING: dict[
    TaskType, Callable[[CeleryTask, int], None]
] = {
    TaskType.SEND_EMAIL: async_send_email_task,
    TaskType.REMINDER_EMAIL: async_reminder_email_task,
}


@register_task_factory(name="execute_tasks")
def execute_tasks_async(self: CeleryTask, task_ids: list[int]) -> None:
    """Execute a list of tasks asynchronously.

    Args:
        self: Celery task instance
        task_ids: List of task IDs to execute
    """
    execute_tasks(self.session, task_ids)
    self.session.commit()


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
        task_to_execute.delay(task.id, **task.arguments)  # type: ignore
