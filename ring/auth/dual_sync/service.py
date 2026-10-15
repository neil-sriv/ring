"""Dual-write and dual-read against the genesis identity service.

Ring's ``user`` table stays authoritative. These helpers never raise to the
caller: failures are logged and counted. Dual-read never serves identity-
service data to the client. Ring writes the IdP (or whichever origin is
configured); it does not call AuthN directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import BackgroundTasks
from genesis_idp import (
    Identity,
    IdentityUpsert,
    created_at_equal,
    format_created_at,
)
from loguru import logger

from ring.auth.dual_sync.metrics import DualSyncSnapshot, metrics
from ring.auth.idp_client.factory import get_identity_client
from ring.fastapp.config import get_config
from ring.parties.models.user_model import User

_DIFF_FIELDS = (
    "external_id",
    "email",
    "name",
    "admin",
    "created_at",
    "credential_present",
)


@dataclass(frozen=True)
class LocalIdentity:
    """Primitive snapshot so background work does not touch the ORM."""

    external_id: str
    email: str
    name: str | None
    hashed_password: str
    admin: bool
    created_at: datetime | None

    @property
    def credential_present(self) -> bool:
        """True when Ring has a stored password hash."""
        return bool(self.hashed_password)


def local_identity_from_user(user: User) -> LocalIdentity:
    """Copy the fields the identity service stores. Uses ``usr_`` id."""
    name = user.name
    if isinstance(name, str) and not name.strip():
        name = None
    return LocalIdentity(
        external_id=user.api_identifier,
        email=user.email,
        name=name,
        hashed_password=user.hashed_password,
        admin=bool(user.admin),
        created_at=user.created_at,
    )


def diff_identity(
    local: LocalIdentity,
    remote: Identity | None,
) -> list[str]:
    """Diff the six contract fields. ``['missing']`` if remote is None.

    Does not compare service ``id`` or ``updated_at``. Does not log hashes.
    """
    if remote is None:
        return ["missing"]
    diffs: list[str] = []
    if local.external_id != remote.external_id:
        diffs.append("external_id")
    if local.email.lower() != remote.email.lower():
        diffs.append("email")
    if (local.name or None) != (remote.name or None):
        diffs.append("name")
    if local.admin != remote.admin:
        diffs.append("admin")
    if not created_at_equal(local.created_at, remote.created_at):
        diffs.append("created_at")
    if local.credential_present != remote.credential_present:
        diffs.append("credential_present")
    return diffs


def schedule_identity_upsert(
    background_tasks: BackgroundTasks,
    user: User,
) -> None:
    """After a successful Ring commit, PUT the full identity."""
    if not get_config().AUTH_DUAL_WRITE:
        return
    local = local_identity_from_user(user)
    background_tasks.add_task(run_identity_upsert, local)


def schedule_identity_compare(
    background_tasks: BackgroundTasks,
    user: User,
) -> None:
    """After a successful legacy read, GET the identity and log diffs."""
    if not get_config().AUTH_DUAL_READ:
        return
    local = local_identity_from_user(user)
    background_tasks.add_task(run_identity_compare, local)


def run_identity_upsert(local: LocalIdentity) -> bool:
    """Upsert one identity. Swallows all errors. True on success."""
    client = get_identity_client()
    if client is None:
        metrics.record_write_skipped()
        logger.warning(
            "auth.dual_write skipped external_id={} reason=not_configured",
            local.external_id,
        )
        return False
    payload = IdentityUpsert(
        external_id=local.external_id,
        email=local.email,
        name=local.name,
        hashed_password=local.hashed_password,
        admin=local.admin,
        created_at=format_created_at(local.created_at),
    )
    try:
        client.upsert_identity(payload)
    except Exception:
        metrics.record_write_failure()
        logger.exception(
            "auth.dual_write failure external_id={} email={}",
            local.external_id,
            local.email,
        )
        _log_write_rate(metrics.snapshot())
        return False
    metrics.record_write_success()
    logger.info(
        "auth.dual_write success external_id={} email={}",
        local.external_id,
        local.email,
    )
    _log_write_rate(metrics.snapshot())
    return True


def run_identity_compare(local: LocalIdentity) -> None:
    """GET the identity and log missing / field mismatch. Never returns it."""
    client = get_identity_client()
    if client is None:
        logger.warning(
            "auth.dual_read skipped external_id={} reason=not_configured",
            local.external_id,
        )
        return
    try:
        remote = client.get_identity(local.external_id)
    except Exception:
        metrics.record_read_failure()
        logger.exception(
            "auth.dual_read failure external_id={}",
            local.external_id,
        )
        return
    diffs = diff_identity(local, remote)
    if diffs == ["missing"]:
        metrics.record_read_missing()
        logger.warning(
            "auth.dual_read missing external_id={} email={}",
            local.external_id,
            local.email,
        )
    elif diffs:
        metrics.record_read_mismatch()
        logger.warning(
            "auth.dual_read mismatch external_id={} fields={}",
            local.external_id,
            ",".join(diffs),
        )
    else:
        metrics.record_read_match()
        logger.info(
            "auth.dual_read match external_id={}",
            local.external_id,
        )
    snapshot = metrics.snapshot()
    logger.info(
        "auth.dual_read stats drift_count={} missing={} mismatches={}",
        snapshot.drift_count,
        snapshot.read_missing,
        snapshot.read_mismatches,
    )


def _log_write_rate(snapshot: DualSyncSnapshot) -> None:
    rate = snapshot.write_success_rate
    rate_text = "n/a" if rate is None else f"{rate:.3f}"
    logger.info(
        "auth.dual_write stats successes={} failures={} skipped={} "
        "success_rate={}",
        snapshot.write_successes,
        snapshot.write_failures,
        snapshot.write_skipped,
        rate_text,
    )


assert _DIFF_FIELDS == (
    "external_id",
    "email",
    "name",
    "admin",
    "created_at",
    "credential_present",
)
