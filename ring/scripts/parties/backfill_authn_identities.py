"""Idempotent backfill: upsert every Ring user into the identity service."""

from __future__ import annotations

from loguru import logger
from sqlalchemy import select

from ring.auth.dual_sync.service import (
    local_identity_from_user,
    run_identity_upsert,
)
from ring.parties.models.user_model import User
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    dry_run: bool = True,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> dict[str, int | bool]:
    """PUT every user by ``usr_`` api_identifier.

    Sends the stored ``hashed_password`` verbatim (never plaintext). The
    identity service ignores ``created_at`` on later upserts.

    Args:
        dry_run: When True, log intended upserts without calling the service.
        deps: Script dependencies with a database session.

    Returns:
        Counts of users considered, upserted, and failed.
    """
    users = list(deps.db.scalars(select(User)).all())
    logger.info(
        "auth.dual_write backfill starting users={} dry_run={}",
        len(users),
        dry_run,
    )
    succeeded = 0
    failed = 0
    for user in users:
        local = local_identity_from_user(user)
        if dry_run:
            logger.info(
                "auth.dual_write backfill would upsert external_id={} "
                "email={}",
                local.external_id,
                local.email,
            )
            succeeded += 1
            continue
        if run_identity_upsert(local):
            succeeded += 1
        else:
            failed += 1
    logger.info(
        "auth.dual_write backfill done dry_run={} succeeded={} failed={}",
        dry_run,
        succeeded,
        failed,
    )
    return {
        "users": len(users),
        "succeeded": succeeded,
        "failed": failed,
        "dry_run": int(dry_run),
    }
