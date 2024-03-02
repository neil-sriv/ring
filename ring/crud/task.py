from __future__ import annotations

from typing import Callable, Sequence
from sqlalchemy.orm import Session
from ring.email_util import construct_email, send_email
from ring.postgres_models import Task
from ring.postgres_models.task_model import SendEmailTask, TaskStatus, TaskType
from ring.sqlalchemy_base import get_db
from ring.worker.celery_app import register_task_factory  # type: ignore
from ring.crud import letter as letter_crud


def execute_send_email_task(db: Session, task: SendEmailTask) -> None:
    group = task.schedule.group
    letter_to_send = group.letters[-1]
    send_email(
        construct_email(
            [u.email for u in letter_to_send.participants],
            letter_to_send.number,
            group.name,
            letter_crud.compile_letter_dict(letter_to_send),
        )
    )
    task.status = TaskStatus.COMPLETED
    db.add(task)
    db.commit()


TASK_TO_EXECUTE_MAPPING: dict[TaskType, Callable[..., None]] = {
    TaskType.SEND_EMAIL: execute_send_email_task,
}


@register_task_factory(name="execute_tasks")
def execute_tasks_async(tasks: Sequence[Task]) -> None:
    db = next(get_db())
    execute_tasks(db, tasks)


def execute_tasks(
    db: Session, tasks: Sequence[Task], execute_async: bool = False
) -> None:
    if execute_async:
        execute_tasks_async.delay(tasks)  # type: ignore
    for task in tasks:
        task_type = TaskType(task.type)
        task_to_execute = TASK_TO_EXECUTE_MAPPING[task_type]
        task_to_execute(db, task)
