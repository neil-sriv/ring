from __future__ import annotations

import logging
from datetime import UTC
from functools import wraps
from typing import Any, Callable, TypeVar

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from sqlalchemy.orm import Session

from ring.async_scheduler.job_registry import register_job
from ring.async_scheduler.schedule import register_interval_job_schedule
from ring.fastapp.config import RingConfig, get_config
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


class APSchedulerLoguruHandler(logging.Handler):
    """Custom logging handler that properly formats APScheduler log messages through loguru."""

    def emit(self, record):
        # Format the message properly
        msg = self.format(record)
        # Map logging levels to loguru levels
        level_map = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }
        level = level_map.get(record.levelno, "INFO")
        logger.log(level, msg)


# Configure APScheduler's logger to use our custom handler
apscheduler_logger = logging.getLogger("apscheduler")
apscheduler_logger.handlers.clear()  # Remove any existing handlers
apscheduler_logger.addHandler(APSchedulerLoguruHandler())
apscheduler_logger.setLevel(logging.DEBUG)


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
    logger=apscheduler_logger,
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

        register_job(name, func)
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
        def wrapper(*args: Any, **func_kwargs: Any) -> JOB_RETURN_TYPE:
            return func(*args, **func_kwargs)

        wrapper.name = name

        # Register the job with interval parameters for later scheduling
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
