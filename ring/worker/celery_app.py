# type: ignore
import os

from celery import Celery
from celery.schedules import crontab

from ring.sqlalchemy_base import SessionLocal
from sqlalchemy.orm import Session
from ring.worker.celery_imports import CELERY_IMPORTS


def celerybeat_schedule() -> dict:
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


class CeleryTask(celery.Task):
    def __init__(self):
        super().__init__()
        self.sessions: dict[str, Session] = {}

    def before_start(self, task_id: str, args, kwargs):
        self.sessions[task_id] = SessionLocal()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session = self.sessions.pop(task_id)
        session.close()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self) -> Session:
        return self.sessions[self.request.id]


def register_task_factory(*dec_args, **dec_kwargs):
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
