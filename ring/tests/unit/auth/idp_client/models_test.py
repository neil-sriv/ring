"""Identity write/read shapes (v2). Hash is write-only."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ring.auth.idp_client.models import (
    Identity,
    IdentityPatch,
    IdentityUpsert,
)

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


def test_upsert_body_includes_hash_and_rejects_plaintext() -> None:
    body = _upsert().request_body()
    assert body["hashed_password"] == HASH
    assert body["hashed_password"].startswith("$")  # type: ignore[union-attr]
    with pytest.raises(ValidationError):
        _upsert(hashed_password="not-a-hash-at-all-plain")
    with pytest.raises(ValidationError):
        _upsert(extra_field="nope")  # type: ignore[call-arg]


def test_identity_get_shape_has_credential_present_not_hash() -> None:
    identity = Identity.model_validate(
        {
            "id": "usr_idp_1",
            "external_id": "usr_1",
            "email": "a@example.com",
            "name": "A",
            "admin": False,
            "credential_present": True,
            "created_at": CREATED,
            "updated_at": "2026-10-15T02:35:00Z",
            "hashed_password": HASH,
        }
    )
    dumped = identity.model_dump()
    assert dumped["credential_present"] is True
    assert "hashed_password" not in dumped
    assert set(dumped) == {
        "id",
        "external_id",
        "email",
        "name",
        "admin",
        "credential_present",
        "created_at",
        "updated_at",
    }


def test_patch_hash_is_optional() -> None:
    empty = IdentityPatch()
    assert empty.request_body() == {}
    name_only = IdentityPatch(name=None)
    assert name_only.request_body() == {"name": None}
    with_hash = IdentityPatch(hashed_password=HASH, admin=True)
    assert with_hash.request_body() == {
        "hashed_password": HASH,
        "admin": True,
    }
    with pytest.raises(ValidationError):
        IdentityPatch(hashed_password="plaintext-password-xx")
