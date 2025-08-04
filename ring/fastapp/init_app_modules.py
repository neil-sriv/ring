from __future__ import annotations

from loguru import logger

from ring.search._gen.all_search_registration import (
    import_all_search_registrations,
)


def init_app_modules() -> None:
    from ring.fastapp._gen.all_jobs import schedule_all_interval_jobs

    """Initialize all app modules.

    This function is called when the app is initialized. It calls all functions in
    the manually (for now) generated _gen.all_ files.
    """

    logger.info("Initializing app modules")

    init_offline_modules()
    schedule_all_interval_jobs()

    import_all_search_registrations()


def init_offline_modules() -> None:
    from ring.fastapp._gen.all_jobs import initialize as initialize_all_jobs
    from ring.fastapp._gen.all_sqla_models import import_all_sqla_models

    import_all_sqla_models()
    initialize_all_jobs()
