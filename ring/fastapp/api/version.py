"""Public deploy-diagnostic version endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ring.async_scheduler import heartbeat
from ring.async_scheduler.scheduler import scheduler
from ring.fastapp.config import get_config
from ring.fastapp.schemas.version import SchedulerStatus, VersionResponse
from ring.lib.version_info import get_version

router = APIRouter()


def _scheduler_status() -> SchedulerStatus:
    return SchedulerStatus(
        enabled=not get_config().DISABLE_SCHEDULER,
        running=bool(scheduler.running),
        last_poll_completed_at=heartbeat.last_poll_completed_at(),
    )


@router.get(
    "/version",
    response_model=VersionResponse,
    operation_id="readVersion",
)
def read_version() -> VersionResponse:
    """Return git commit metadata, image identities, and scheduler health.

    Unauthenticated so a host-side `curl` can tell which commit and images
    are actually running after a deploy, and whether the letter scheduler
    is alive. Version metadata is cached briefly in-process; the scheduler
    status is computed fresh on every request.
    """
    return get_version().model_copy(update={"scheduler": _scheduler_status()})
