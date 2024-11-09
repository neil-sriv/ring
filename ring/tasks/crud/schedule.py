from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Sequence

import sqlalchemy
from sqlalchemy import or_, select

from ring.api_identifier import util as api_identifier_crud
from ring.parties.models.group_model import Group
from ring.tasks.crud import task as task_crud
from ring.tasks.models.schedule_model import Schedule
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.worker.celery_app import (  # type: ignore
    CeleryTask,
    register_task_factory,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_schedule_for_group(db: Session, group_api_id: str) -> Schedule:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return group.schedule


def register_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime.datetime,
    arguments: dict[str, str] | None = None,
) -> Task:
    if not arguments:
        arguments = {}
    task = Task.create(schedule, task_type, execute_at, arguments)
    schedule.tasks.append(task)
    db.add(task)
    return task


def unregister_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime.datetime,
):
    task = db.scalars(
        sqlalchemy.select(Task).where(
            Task.schedule_id == schedule.id,
            Task.type == task_type,
            Task.status == TaskStatus.PENDING,
            Task.execute_at == execute_at,
        )
    ).one_or_none()
    if task:
        print("deleting task:", task)
        db.delete(task)


def update_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime.datetime,
    new_execute_at: datetime.datetime,
    arguments: dict[str, str] | None = None,
) -> Task | None:
    task = db.scalars(
        sqlalchemy.select(Task).where(
            Task.schedule_id == schedule.id,
            Task.type == task_type,
            Task.status == TaskStatus.PENDING,
            Task.execute_at == execute_at,
        )
    ).one_or_none()
    print("found task:", task)
    if not task:
        return None
    task.execute_at = new_execute_at
    if arguments:
        task.arguments = arguments

    return task


def collect_pending_tasks(
    db: Session,
    recent_time: datetime.datetime,
) -> Sequence[Task]:
    tasks = db.scalars(
        select(Task)
        .where(
            or_(Task.execute_at < recent_time, Task.execute_at == recent_time),
            Task.status == TaskStatus.PENDING,
        )
        .order_by(Task.schedule_id, Task.type, Task.execute_at)
    ).all()

    return tasks


@register_task_factory(name="poll_schedule")
def poll_schedule_task(self: CeleryTask) -> dict[str, str]:
    from ring.letters.crud.letter import (
        collect_future_letters,
        postpend_upcoming_letters,
        promote_and_create_new_letters,
    )
    from ring.tasks.crud import schedule as schedule_crud

    time.sleep(5)

    curr_time = datetime.datetime.now(datetime.UTC)
    tasks = schedule_crud.collect_pending_tasks(self.session, curr_time)
    if tasks:
        task_crud.execute_tasks_async.delay(
            [task.id for task in tasks],
        )

    postpend, promote = collect_future_letters(
        self.session, curr_time + datetime.timedelta(days=7)
    )
    if postpend:
        postpend_upcoming_letters.delay(
            [letter.id for letter in postpend],
        )
    if promote:
        promote_and_create_new_letters.delay(
            [letter.id for letter in promote],
        )

    return {
        "status": "success",
        "message": f"task ids: {[task.id for task in tasks]}, postpend letter ids: {[letter.id for letter in postpend]}, promote letter ids: {[letter.id for letter in promote]}",
        "task_name": "poll_schedule",
    }
