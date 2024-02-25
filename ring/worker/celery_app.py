# type: ignore
import os
from typing import Any
from datetime import datetime
import time

from celery import Celery
from celery.schedules import crontab

from ring.sqlalchemy_base import get_db
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

        # celery.register_task(f)
        return wrapper

    return decorator


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender: Any, **kwargs: Any):
#     sender.add_periodic_task(
#         crontab(minute="*/1"), poll_schedule_task.s(), name="poll_schedule"
#     )
