from __future__ import annotations

from loguru import logger


def init_app_modules() -> None:
    """Initialize all app modules.

    Imports generated registries and schedules interval jobs. Called from
    ``create_app``.
    """
    from ring.async_scheduler.schedule import schedule_all_interval_jobs

    logger.info("Initializing app modules")

    init_offline_modules()
    schedule_all_interval_jobs()


def init_offline_modules() -> None:
    from ring.fastapp._gen.all_jobs import initialize as initialize_all_jobs
    from ring.fastapp._gen.all_sqla_models import import_all_sqla_models
    from ring.search._gen.all_search_registration import (
        import_all_search_registrations,
    )

    import_all_sqla_models()
    initialize_all_jobs()
    import_all_search_registrations()
