from __future__ import annotations


def import_all_jobs() -> None:
    """Import all jobs."""
    from ring.letters.crud.letter import (
        postpend_upcoming_letters,
        promote_and_create_new_letters,
    )
    from ring.parties.crud.authn import email_password_reset
    from ring.parties.crud.invite import email_user_invites
    from ring.search.crud.integrity import (
        async_check_integrity_for_searchable_type,
        search_integrity_check,
    )
    from ring.tasks.crud.schedule import poll_schedule_task
    from ring.tasks.crud.task import (
        async_reminder_email_task,
        async_send_email_task,
        execute_tasks_async,
    )


def schedule_all_interval_jobs() -> None:
    """Schedule all interval jobs."""
    from ring.async_scheduler.schedule import INTERVAL_JOB_SCHEDULE_REGISTRY
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


def initialize() -> None:
    import_all_jobs()
