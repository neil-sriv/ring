"""CRUD operations and scheduling utilities for Ring's task system.

This module provides functions for managing schedules and their associated tasks,
including task registration, updates, and polling for pending tasks. It also
handles the periodic scheduling of letter-related operations.
"""

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
    """Get a group's schedule by the group's API identifier.

    Args:
        db: Database session
        group_api_id: API identifier of the group

    Returns:
        Schedule: The group's schedule

    Raises:
        NoResultFound: If no group is found with the given API ID
    """
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return group.schedule


def register_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime.datetime,
    arguments: dict[str, str] | None = None,
) -> Task:
    """Register a new task with a schedule.

    Args:
        db: Database session
        schedule: Schedule to register the task with
        task_type: Type of task to register
        execute_at: When the task should be executed
        arguments: Optional arguments for task execution

    Returns:
        Task: The newly created task
    """
    if not arguments:
        arguments = {}
    task = Task.create(schedule, task_type, execute_at, arguments)
    db.add(task)
    schedule.tasks.append(task)
    return task


def unregister_task(
    db: Session,
    schedule: Schedule,
    task_type: TaskType,
    execute_at: datetime.datetime,
):
    """Remove a pending task from a schedule.

    Args:
        db: Database session
        schedule: Schedule to remove the task from
        task_type: Type of task to remove
        execute_at: Execution time of the task to remove
    """
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
    """Update a pending task's execution time and arguments.

    Args:
        db: Database session
        schedule: Schedule containing the task
        task_type: Type of task to update
        execute_at: Current execution time of the task
        new_execute_at: New execution time for the task
        arguments: Optional new arguments for task execution

    Returns:
        Task | None: The updated task, or None if no matching task is found
    """
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
    """Collect all pending tasks that should be executed by a given time.

    Tasks are ordered by schedule ID, type, and execution time to ensure
    consistent processing order.

    Args:
        db: Database session
        recent_time: Collect tasks scheduled up to this time

    Returns:
        Sequence[Task]: List of pending tasks to execute
    """
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
    """Celery task for polling schedules and executing pending tasks.

    This task:
    1. Collects and executes pending tasks
    2. Identifies letters that need to be postpended or promoted
    3. Schedules letter-related operations asynchronously

    Args:
        self: Celery task instance

    Returns:
        dict[str, str]: Status report including task and letter IDs processed
    """
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
