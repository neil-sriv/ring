from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# from ring.apscheduler.scheduler import JOB_RETURN_TYPE
from loguru import logger

from ring.lib.util import RegistrationDict

INTERVAL_JOB_SCHEDULE_REGISTRY: RegistrationDict[str, IntervalJobSchedule] = (
    RegistrationDict("INTERVAL_JOB_SCHEDULE_REGISTRY")
)


@dataclass
class IntervalJobSchedule:
    job: Callable[..., Any]
    kwargs: dict[str, Any]


def register_interval_job_schedule(
    name: str,
    job: Callable[..., Any],
    **kwargs: Any,
) -> None:
    """Register a job schedule.

    Args:
        name: The name of the job schedule.
        job: The job to register.
        seconds: The number of seconds to wait between job executions.
        minutes: The number of minutes to wait between job executions.
        hours: The number of hours to wait between job executions.
    """
    INTERVAL_JOB_SCHEDULE_REGISTRY[name] = IntervalJobSchedule(
        job=job,
        kwargs=kwargs,
    )


def schedule_all_interval_jobs() -> None:
    """Replace the scheduler's interval jobs from the registry."""
    from ring.async_scheduler.scheduler import scheduler

    scheduler.remove_all_jobs()

    for job_name, job_info in INTERVAL_JOB_SCHEDULE_REGISTRY.items():
        scheduler.add_job(
            job_info.job,
            id=job_name,
            trigger="interval",
            replace_existing=True,
            **job_info.kwargs,
        )
