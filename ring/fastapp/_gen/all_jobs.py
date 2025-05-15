from __future__ import annotations


def import_all_jobs() -> None:
    """Import all jobs."""
    from ring.tasks.crud.schedule import poll_schedule_task


def schedule_all_interval_jobs() -> None:
    """Schedule all interval jobs."""
    from ring.apscheduler.schedule import INTERVAL_JOB_SCHEDULE_REGISTRY
    from ring.apscheduler.scheduler import scheduler

    scheduler.remove_all_jobs()

    for job_name, job_info in INTERVAL_JOB_SCHEDULE_REGISTRY.items():
        scheduler.add_job(
            job_info.job,
            id=job_name,
            trigger="interval",
            replace_existing=True,
            **job_info.kwargs,
        )


def initialize() -> None:
    import_all_jobs()
    schedule_all_interval_jobs()
