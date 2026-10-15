"""Blindfold heartbeat as an APScheduler interval job.

The scheduler runs inside the API process (see ``ring.fastapp.fast``
lifespan and ``compose.prod.yml``). This is not a separate worker.
``minutes`` stays locked to ``INTERVAL_SECONDS``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.async_scheduler.scheduler import interval_job_factory
from ring.lib.blindfold_heartbeat import INTERVAL_SECONDS, run_heartbeat


@interval_job_factory(
    "blindfold_heartbeat",
    minutes=INTERVAL_SECONDS // 60,
)
def blindfold_heartbeat(db: Session) -> None:
    """Send one beat every five minutes.

    The scheduler injects ``db`` and this job does not query it. No-op
    unless ``HEARTBEAT_URL``, ``HEARTBEAT_KEY_ID``, and
    ``HEARTBEAT_SECRET`` are set. An ok beat means this job ran and
    ``GET /`` on this process returned 2xx.
    """
    del db
    run_heartbeat()
