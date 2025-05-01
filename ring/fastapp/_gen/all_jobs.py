from __future__ import annotations

from dataclasses import asdict

from ring.lib.logger import logger


def import_all_jobs() -> None:
    """Import all jobs."""
    from ring.tasks.crud.schedule import poll_schedule_task


def schedule_all_interval_jobs() -> None:
    """Schedule all interval jobs."""
    from ring.apscheduler.schedule import INTERVAL_JOB_SCHEDULE_REGISTRY
    from ring.apscheduler.scheduler import scheduler

    for job_name, job_info in INTERVAL_JOB_SCHEDULE_REGISTRY.items():
        kwargs_if_not_none = {
            k: v for k, v in asdict(job_info).items() if v is not None
        }
        scheduler.add_job(
            id=job_name,
            trigger="interval",
            replace_existing=True,
            **kwargs_if_not_none,
        )


def initialize() -> None:
    import_all_jobs()
    schedule_all_interval_jobs()
