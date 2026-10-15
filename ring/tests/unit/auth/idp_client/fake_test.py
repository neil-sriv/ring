"""Fake IdentityClient behaviour (v2)."""

from __future__ import annotations

import pytest

from ring.auth.idp_client.errors import IdentityClientError
from ring.auth.idp_client.fake import FakeIdentityClient
from ring.auth.idp_client.models import IdentityPatch, IdentityUpsert

HASH = "$2b$12$" + ("a" * 53)
CREATED = "2024-01-15T12:00:00Z"


def _upsert(**overrides: object) -> IdentityUpsert:
    values: dict[str, object] = {
        "external_id": "usr_1",
        "email": "a@example.com",
        "name": "A",
        "hashed_password": HASH,
        "admin": False,
        "created_at": CREATED,
    }
    values.update(overrides)
    return IdentityUpsert(**values)  # type: ignore[arg-type]


def test_fake_upsert_is_idempotent() -> None:
    client = FakeIdentityClient()
    client.upsert_identity(_upsert())
    updated = client.upsert_identity(
        _upsert(email="b@example.com", name="B", admin=True)
    )
    assert updated.email == "b@example.com"
    assert updated.admin is True
    assert updated.credential_present is True
    assert "hashed_password" not in updated.model_dump()
    assert client.hashes["usr_1"] == HASH
    assert client.get_identity_by_email("b@example.com") is not None


def test_fake_create_conflicts_and_patch() -> None:
    client = FakeIdentityClient()
    client.create_identity(_upsert())
    with pytest.raises(IdentityClientError) as exc_info:
        client.create_identity(_upsert())
    assert exc_info.value.status_code == 409
    with pytest.raises(IdentityClientError) as email_conflict:
        client.create_identity(_upsert(external_id="usr_2"))
    assert email_conflict.value.status_code == 409
    patched = client.patch_identity("usr_1", IdentityPatch(name=None))
    assert patched.name is None
    assert patched.credential_present is True
    assert "hashed_password" not in patched.model_dump()
    other_hash = "$2b$12$" + ("b" * 53)
    with_hash = client.patch_identity(
        "usr_1", IdentityPatch(hashed_password=other_hash)
    )
    assert with_hash.credential_present is True
    assert client.hashes["usr_1"] == other_hash
    by_email = client.get_identity_by_email("A@Example.com")
    assert by_email is not None
    assert by_email.external_id == "usr_1"


def test_fake_can_fail_and_miss() -> None:
    client = FakeIdentityClient()
    client.fail_upserts = True
    with pytest.raises(IdentityClientError):
        client.upsert_identity(_upsert())
    client.fail_upserts = False
    client.upsert_identity(_upsert())
    client.missing_reads = True
    assert client.get_identity("usr_1") is None
    client.missing_reads = False
    client.fail_reads = True
    with pytest.raises(IdentityClientError):
        client.get_identity("usr_1")


def test_fake_credential_store_unavailable() -> None:
    client = FakeIdentityClient()
    client.credential_store_failures_remaining = 1
    with pytest.raises(IdentityClientError) as exc_info:
        client.upsert_identity(_upsert())
    assert exc_info.value.error == "credential_store_unavailable"
    created = client.upsert_identity(_upsert())
    assert created.credential_present is True
