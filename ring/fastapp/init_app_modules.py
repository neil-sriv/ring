from __future__ import annotations

from ring.fastapp._gen.all_jobs import initialize as initialize_all_jobs
from ring.lib.logger import logger
from ring.search._gen.all_search_registration import (
    import_all_search_registrations,
)


def init_app_modules() -> None:
    """Initialize all app modules.

    This function is called when the app is initialized. It calls all functions in
    the manually (for now) generated _gen.all_ files.
    """
    from ring.fastapp._gen.all_sqla_models import import_all_sqla_models

    logger.info("Initializing app modules")
    import_all_sqla_models()
    initialize_all_jobs()

    import_all_search_registrations()
