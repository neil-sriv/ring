from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.schedule_model import Schedule
from ring.postgres_models.group_model import Group
from ring.postgres_models.task_model import Task, TaskType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_schedule_for_group(db: Session, group_api_id: str) -> Schedule:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return group.schedule


def register_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime,
    arguments: dict[str, str],
) -> Task:
    task = Task.create(schedule, task_type, execute_at, arguments)
    schedule.tasks.append(task)
    db.add(task)
    return task
