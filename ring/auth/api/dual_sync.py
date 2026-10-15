"""Admin visibility into identity-service dual-sync."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ring.auth.dual_sync.metrics import metrics
from ring.auth.idp_client.factory import identity_client_config_from_ring
from ring.auth.schemas.dual_sync import DualSyncStats
from ring.fastapp.config import get_config
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)

router = APIRouter()


@router.get(
    "/auth/dual-sync/stats",
    response_model=DualSyncStats,
    operation_id="readAuthDualSyncStats",
)
async def read_dual_sync_stats(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> DualSyncStats:
    """Return dual-write success rate and dual-read drift counts.

    Ring admin only. Counters are process-local and reset on restart.
    """
    if not req_dep.current_user.admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    config = get_config()
    client_config = identity_client_config_from_ring(config)
    snapshot = metrics.snapshot()
    return DualSyncStats(
        dual_write_enabled=config.AUTH_DUAL_WRITE,
        dual_read_enabled=config.AUTH_DUAL_READ,
        identity_configured=client_config.configured,
        write_attempts=snapshot.write_attempts,
        write_successes=snapshot.write_successes,
        write_failures=snapshot.write_failures,
        write_skipped=snapshot.write_skipped,
        write_success_rate=snapshot.write_success_rate,
        read_attempts=snapshot.read_attempts,
        read_matches=snapshot.read_matches,
        read_missing=snapshot.read_missing,
        read_mismatches=snapshot.read_mismatches,
        read_failures=snapshot.read_failures,
        drift_count=snapshot.drift_count,
    )
