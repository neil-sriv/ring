from __future__ import annotations
import datetime
import time
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import and_, or_, select
from ring.crud import api_identifier as api_identifier_crud, task as task_crud
from ring.postgres_models.schedule_model import Schedule
from ring.postgres_models.group_model import Group
from ring.postgres_models.task_model import Task, TaskStatus, TaskType
from ring.sqlalchemy_base import get_db
from ring.worker.celery_app import register_task_factory  # type: ignore

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
    arguments: dict[str, str],
) -> Task:
    task = Task.create(schedule, task_type, execute_at, arguments)
    schedule.tasks.append(task)
    db.add(task)
    return task


def collect_pending_tasks(
    db: Session,
    recent_hour: datetime.datetime,
) -> Sequence[Task]:
    missed_tasks_filter = and_(
        Task.status == TaskStatus.PENDING,
        Task.execute_at < recent_hour,
    )
    scheduled_tasks_filter = and_(
        Task.status == TaskStatus.PENDING, Task.execute_at == recent_hour
    )
    tasks = db.scalars(
        select(Task)
        .filter(or_(missed_tasks_filter, scheduled_tasks_filter))
        .order_by(Task.schedule_id, Task.type, Task.execute_at)
    ).all()

    return tasks


def execute_tasks(
    db: Session, tasks: Sequence[Task], execute_async: bool = False
) -> None:
    task_crud.execute_tasks(db, tasks, execute_async)


@register_task_factory(name="poll_schedule")
def poll_schedule_task():
    from ring.crud import schedule as schedule_crud

    time.sleep(5)
    db = next(get_db())
    hour_floor = datetime.datetime.now(datetime.UTC).replace(
        minute=0, second=0, microsecond=0
    )
    tasks = schedule_crud.collect_pending_tasks(db, hour_floor)
    schedule_crud.execute_tasks(db, tasks, execute_async=True)
    print([task.__dict__ for task in tasks])

    return {
        "status": "success",
        "message": "Group ids emailed:",
        "task_name": "poll_schedule",
    }
