"""Dual-write / dual-read service with a fake identity client."""

from __future__ import annotations

from datetime import UTC, datetime

from genesis_idp import FakeIdentityClient, Identity, IdentityUpsert

from ring.auth.dual_sync.metrics import metrics
from ring.auth.dual_sync.service import (
    LocalIdentity,
    diff_identity,
    run_identity_compare,
    run_identity_upsert,
)
from ring.auth.idp_client.factory import set_identity_client_override

HASH = "$2b$12$" + ("a" * 53)
CREATED = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
CREATED_Z = "2024-01-15T12:00:00Z"


def _local(**kwargs: object) -> LocalIdentity:
    values: dict[str, object] = {
        "external_id": "usr_1",
        "email": "a@example.com",
        "name": "A",
        "hashed_password": HASH,
        "admin": False,
        "created_at": CREATED,
    }
    values.update(kwargs)
    return LocalIdentity(**values)  # type: ignore[arg-type]


def _remote(**overrides: object) -> Identity:
    values: dict[str, object] = {
        "id": "usr_idp_1",
        "external_id": "usr_1",
        "email": "a@example.com",
        "name": "A",
        "admin": False,
        "credential_present": True,
        "created_at": CREATED_Z,
        "updated_at": "2026-10-15T02:35:00Z",
    }
    values.update(overrides)
    return Identity(**values)  # type: ignore[arg-type]


def setup_function() -> None:
    metrics.reset()
    set_identity_client_override(None)


def teardown_function() -> None:
    metrics.reset()
    set_identity_client_override(None)


def test_diff_identity_missing_and_fields() -> None:
    local = _local()
    assert diff_identity(local, None) == ["missing"]
    assert diff_identity(local, _remote()) == []
    diffs = diff_identity(
        local,
        _remote(
            external_id="usr_2",
            email="b@example.com",
            name="B",
            admin=True,
            credential_present=False,
            created_at="2020-01-01T00:00:00Z",
        ),
    )
    assert diffs == [
        "external_id",
        "email",
        "name",
        "admin",
        "created_at",
        "credential_present",
    ]


def test_diff_does_not_include_id_or_updated_at() -> None:
    local = _local()
    assert (
        diff_identity(
            local,
            _remote(id="usr_other", updated_at="1999-01-01T00:00:00Z"),
        )
        == []
    )


def test_upsert_success_and_failure_are_counted() -> None:
    fake = FakeIdentityClient()
    set_identity_client_override(fake)
    assert run_identity_upsert(_local()) is True
    assert fake.upsert_calls[0].hashed_password == HASH
    assert fake.upsert_calls[0].hashed_password.startswith("$")
    assert metrics.snapshot().write_successes == 1
    fake.fail_upserts = True
    assert run_identity_upsert(_local()) is False
    snapshot = metrics.snapshot()
    assert snapshot.write_attempts == 2
    assert snapshot.write_failures == 1
    assert snapshot.write_success_rate == 0.5


def test_upsert_skipped_when_unconfigured() -> None:
    assert run_identity_upsert(_local()) is False
    snapshot = metrics.snapshot()
    assert snapshot.write_skipped == 1
    assert snapshot.write_attempts == 0


def test_compare_match_missing_mismatch_failure() -> None:
    fake = FakeIdentityClient()
    set_identity_client_override(fake)
    fake.upsert_identity(
        IdentityUpsert(
            external_id="usr_1",
            email="a@example.com",
            name="A",
            hashed_password=HASH,
            admin=False,
            created_at=CREATED_Z,
        )
    )
    run_identity_compare(_local())
    assert metrics.snapshot().read_matches == 1

    fake.identities["usr_1"] = _remote(email="other@example.com")
    run_identity_compare(_local())
    assert metrics.snapshot().read_mismatches == 1

    fake.missing_reads = True
    run_identity_compare(_local())
    assert metrics.snapshot().read_missing == 1
    fake.missing_reads = False

    fake.fail_reads = True
    run_identity_compare(_local())
    assert metrics.snapshot().read_failures == 1
    assert metrics.snapshot().drift_count == 2
