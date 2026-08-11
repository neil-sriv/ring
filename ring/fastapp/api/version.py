"""Public deploy-diagnostic version endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ring.fastapp.schemas.version import VersionResponse
from ring.lib.version_info import get_version

router = APIRouter()


@router.get(
    "/version",
    response_model=VersionResponse,
    operation_id="readVersion",
)
def read_version() -> VersionResponse:
    """Return git commit metadata and Docker image identities.

    Unauthenticated so a host-side `curl` can tell which commit and images
    are actually running after a deploy. Cached briefly in-process so
    repeated public hits do not shell out to git on every request.
    """
    return get_version()
