from __future__ import annotations

from datetime import UTC

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

jobstores = {
    "memory": MemoryJobStore(),
    "sqla": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite"),
}
executors = {
    "threadpool": ThreadPoolExecutor(1),
    "processpool": ProcessPoolExecutor(1),
}
job_defaults = {"coalesce": False, "max_instances": 1}

scheduler = BackgroundScheduler()

scheduler.configure(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=UTC,
)
