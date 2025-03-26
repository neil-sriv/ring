"""Celery configuration and task base classes for Ring.

This module sets up Celery for Ring's asynchronous task processing, including
configuration, task base classes, and task registration utilities.
"""

# type: ignore
import os
from typing import Any

from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session

from ring.config import RingConfig, get_config
from ring.sqlalchemy_base import SessionLocal
from ring.worker.celery_imports import CELERY_IMPORTS


def celerybeat_schedule() -> dict:
    """Define the Celery beat schedule for periodic tasks.

    This function configures the schedule for periodic tasks that should be
    executed by Celery beat. Currently includes:
    - poll_schedule: Runs on a cron schedule to check for pending tasks

    Returns:
        dict: Schedule configuration mapping task names to their execution schedules
    """
    return {
        "poll_schedule": {
            "task": "poll_schedule",
            "schedule": crontab(),
        }
    }


celery = Celery(
    "celery",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis"),
    imports=CELERY_IMPORTS,
    beat_schedule=celerybeat_schedule(),
)

celery.conf.update(
    result_expires=3600,
    concrrency=1,
    worker_max_memory_per_child=120000,  # 120MB
)


class CeleryTask(celery.Task):
    """Base class for Ring Celery tasks.

    This class extends Celery's Task class to provide database session management
    and Ring configuration access for all tasks.

    Attributes:
        sessions (dict[str, Session]): Task-specific database sessions
        config (RingConfig): Ring configuration
    """

    def __init__(self):
        """Initialize the task with empty session storage."""
        super().__init__()
        self.sessions: dict[str, Session] = {}
        self.config: RingConfig = get_config()

    def before_start(self, task_id: str, args, kwargs):
        """Set up task-specific resources before task execution.

        Creates a new database session for the task.

        Args:
            task_id (str): Unique task identifier
            args: Task positional arguments
            kwargs: Task keyword arguments
        """
        self.sessions[task_id] = SessionLocal()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Clean up task-specific resources after task completion.

        Closes and removes the task's database session.

        Args:
            status: Task execution status
            retval: Task return value
            task_id (str): Unique task identifier
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Error information if task failed
        """
        session = self.sessions.pop(task_id)
        session.close()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self) -> Session:
        """Get the database session for the current task.

        Returns:
            Session: SQLAlchemy session for the current task
        """
        return self.sessions[self.request.id]


def register_task_factory(*dec_args: Any, **dec_kwargs: Any) -> Any:
    """Create a decorator for registering Ring Celery tasks.

    This factory function creates a decorator that registers functions as
    Celery tasks with the Ring-specific task base class.

    Args:
        *dec_args: Positional arguments for the Celery task decorator
        **dec_kwargs: Keyword arguments for the Celery task decorator

    Returns:
        Callable: Decorator for registering Celery tasks
    """

    def decorator(f):
        @celery.task(
            *dec_args,
            **dec_kwargs,
            bind=True,
            base=CeleryTask,
        )
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return decorator
