from __future__ import annotations

from ring.fastapp._gen.all_jobs import initialize as initialize_all_jobs
from ring.lib.logger import logger


def init_app_modules() -> None:
    """Initialize all app modules.

    This function is called when the app is initialized. It calls all functions in
    the entrypoint.initialize files.
    """
    from ring.fastapp._gen.all_sqla_models import import_all_sqla_models

    logger.info("Initializing app modules")
    import_all_sqla_models()
    initialize_all_jobs()
