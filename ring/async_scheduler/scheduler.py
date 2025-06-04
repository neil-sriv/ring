from __future__ import annotations

from datetime import UTC
from functools import wraps
from typing import Any, Callable, TypeVar

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from ring.async_scheduler.schedule import register_interval_job_schedule
from ring.fastapp.config import RingConfig, get_config
from ring.lib.logger import logger
from ring.sqlalchemy_base import Base, SessionLocal, db_session, get_db

jobstores = {
    "memory": MemoryJobStore(),
    "sqla": SQLAlchemyJobStore(
        url=get_config().cockroach_database_uri,
        tablename="apscheduler_jobs",
        tableschema="public",
        metadata=Base.metadata,
    ),
}

executors = {
    "threadpool": ThreadPoolExecutor(1),
    # "processpool": ProcessPoolExecutor(1),
}
job_defaults = {"coalesce": False, "max_instances": 1}


class CustomScheduler(BackgroundScheduler):
    def __init__(self) -> None:
        super().__init__()
        self.config: RingConfig = get_config()
        self.sessions: dict[str, Session] = {}

    def add_job(
        self,
        job: Callable[..., T],
        *args: Any,
        jobstore: str = "sqla",
        **kwargs: Any,
    ) -> None:
        logger.info(f"Adding job: {job} {args} {kwargs}")
        super().add_job(
            job,
            *args,
            jobstore=jobstore,
            **kwargs,
        )


scheduler = CustomScheduler()

scheduler.configure(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=UTC,
    logger=logger,
)

JOB_RETURN_TYPE = TypeVar("JOB_RETURN_TYPE")


def job_factory(
    name: str,
) -> Callable[
    [Callable[..., JOB_RETURN_TYPE]], Callable[..., JOB_RETURN_TYPE]
]:
    """A decorator for APScheduler jobs that handles database session management.

    Args:
        name: The name of the job

    Returns:
        A callable that wraps the job function with database session management
    """

    def decorator(
        func: Callable[..., JOB_RETURN_TYPE],
    ) -> Callable[..., JOB_RETURN_TYPE]:
        @db_session
        @wraps(func)
        def wrapper(db: Session, *args: Any, **kwargs: Any) -> JOB_RETURN_TYPE:
            logger.info(f"Running job {name}: {[args]} {[kwargs]}")
            try:
                return func(db, *args, **kwargs)
            finally:
                db.close()

        wrapper.name = name
        return wrapper

    return decorator


def interval_job_factory(
    name: str,
    **kwargs: Any,
) -> Callable[
    [Callable[..., JOB_RETURN_TYPE]], Callable[..., JOB_RETURN_TYPE]
]:
    def decorator(
        func: Callable[..., JOB_RETURN_TYPE],
    ) -> Callable[..., JOB_RETURN_TYPE]:
        @wraps(func)
        @job_factory(name)
        def wrapper(*args: Any, **kwargs: Any) -> JOB_RETURN_TYPE:
            return func(*args, **kwargs)

        wrapper.name = name
        register_interval_job_schedule(name, wrapper, **kwargs)
        return wrapper

    return decorator


@job_factory("test_job")
def test_job(*args: Any, db: Session, **kwargs: Any) -> str:
    return "Hello, World!"


# @interval_job_factory("test_interval_job", seconds=5)
# def test_interval_job(*args: Any, **kwargs: Any) -> str:
#     logger.info("Hello, World!")
#     return "Hello, World!"
