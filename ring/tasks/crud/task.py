from __future__ import annotations

from typing import Callable
from sqlalchemy.orm import Session
from ring.email_util import send_email, construct_html_email
from ring.letters.constants import LetterStatus
from ring.tasks.models.task_model import SendEmailTask, TaskStatus, TaskType, Task
from ring.sqlalchemy_base import get_db
from ring.worker.celery_app import CeleryTask, register_task_factory  # type: ignore
from ring.letters.crud import letter as letter_crud


def execute_send_email_task(db: Session, task: SendEmailTask) -> None:
    group = task.schedule.group
    letter_to_send = sorted(
        [
            letter
            for letter in group.letters
            if letter.status == LetterStatus.IN_PROGRESS
        ],
        key=lambda l: l.number,
    )[-1]
    send_email(
        construct_html_email(
            [u.email for u in letter_to_send.participants],
            letter_to_send.number,
            group.name,
            letter_crud.compile_letter_dict(letter_to_send),
        )
    )
    letter_to_send.status = LetterStatus.SENT
    db.commit()


@register_task_factory(name="send_email_task")
def async_send_email_task(self: CeleryTask, task_id: int) -> None:
    db = next(get_db())
    task = db.query(SendEmailTask).filter(SendEmailTask.id == task_id).one()
    try:
        execute_send_email_task(db, task)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
    else:
        task.status = TaskStatus.COMPLETED
    db.commit()


TASK_TO_EXECUTE_MAPPING: dict[TaskType, Callable[..., None]] = {
    TaskType.SEND_EMAIL: execute_send_email_task,
}

ASYNC_TASK_TO_EXECUTE_MAPPING: dict[TaskType, Callable[..., None]] = {
    TaskType.SEND_EMAIL: async_send_email_task
}


@register_task_factory(name="execute_tasks")
def execute_tasks_async(self: CeleryTask, task_ids: list[int]) -> None:
    db = next(get_db())
    execute_tasks(db, task_ids)


def execute_tasks(
    db: Session, task_ids: list[int], execute_async: bool = False
) -> None:
    if execute_async:
        execute_tasks_async.delay(task_ids)  # type: ignore
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    for task in tasks:
        task.status = TaskStatus.IN_PROGRESS
    db.commit()
    for task in tasks:
        task_type = TaskType(task.type)
        if task_type in ASYNC_TASK_TO_EXECUTE_MAPPING:
            task_to_execute = ASYNC_TASK_TO_EXECUTE_MAPPING[task_type]
            task_to_execute.delay(task.id)  # type: ignore
        else:
            task_to_execute = TASK_TO_EXECUTE_MAPPING[task_type]
            task_to_execute(db, task)
            task.status = TaskStatus.COMPLETED
    db.commit()
