# type: ignore
import os

from celery import Celery
from celery.schedules import crontab

from ring.worker.celery_imports import CELERY_IMPORTS


def celerybeat_schedule() -> dict:
    return {
        "poll_schedule": {
            "task": "poll_schedule",
            "schedule": crontab(minute="*/1"),
        }
    }


celery = Celery(
    "celery",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis"),
    imports=CELERY_IMPORTS,
    beat_schedule=celerybeat_schedule(),
)


def register_task_factory(*dec_args, **dec_kwargs):
    def decorator(f):
        @celery.task(*dec_args, **dec_kwargs)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return decorator
