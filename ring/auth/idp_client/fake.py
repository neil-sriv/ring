"""In-memory IdentityClient for tests and local dual-sync."""

from __future__ import annotations

from datetime import UTC, datetime

from ring.auth.idp_client.errors import IdentityClientError
from ring.auth.idp_client.models import Identity, IdentityPatch, IdentityUpsert
from ring.auth.idp_client.times import format_created_at


class FakeIdentityClient:
    """Stores identities by ``external_id``; optional fail/missing hooks."""

    def __init__(self) -> None:
        self.identities: dict[str, Identity] = {}
        self.hashes: dict[str, str] = {}
        self.upsert_calls: list[IdentityUpsert] = []
        self.create_calls: list[IdentityUpsert] = []
        self.patch_calls: list[tuple[str, IdentityPatch]] = []
        self.get_calls: list[str] = []
        self.get_by_email_calls: list[str] = []
        self.fail_upserts: bool = False
        self.fail_reads: bool = False
        self.missing_reads: bool = False
        self.credential_store_failures_remaining: int = 0

    def upsert_identity(self, payload: IdentityUpsert) -> Identity:
        self.upsert_calls.append(payload)
        self._raise_if_credential_store_down()
        if self.fail_upserts:
            raise IdentityClientError("fake upsert failed")
        return self._store(payload)

    def create_identity(self, payload: IdentityUpsert) -> Identity:
        self.create_calls.append(payload)
        if payload.external_id in self.identities or self._email_owner(
            payload.email
        ):
            raise IdentityClientError(
                "http 409",
                status_code=409,
                error="conflict",
            )
        self._raise_if_credential_store_down()
        return self._store(payload)

    def patch_identity(
        self, external_id: str, payload: IdentityPatch
    ) -> Identity:
        self.patch_calls.append((external_id, payload))
        existing = self.identities.get(external_id)
        if existing is None:
            raise IdentityClientError(
                "http 404",
                status_code=404,
                error="not_found",
            )
        if "hashed_password" in payload.model_fields_set:
            self._raise_if_credential_store_down()
        now = format_created_at(datetime.now(UTC))
        email = (
            payload.email
            if "email" in payload.model_fields_set and payload.email
            else existing.email
        )
        name = existing.name
        if "name" in payload.model_fields_set:
            name = payload.name
        admin = (
            payload.admin
            if "admin" in payload.model_fields_set
            and payload.admin is not None
            else existing.admin
        )
        if (
            "hashed_password" in payload.model_fields_set
            and payload.hashed_password
        ):
            self.hashes[external_id] = payload.hashed_password
        identity = Identity(
            id=existing.id,
            external_id=external_id,
            email=email,
            name=name,
            admin=admin,
            credential_present=external_id in self.hashes,
            created_at=existing.created_at,
            updated_at=now,
        )
        self.identities[external_id] = identity
        return identity

    def get_identity(self, external_id: str) -> Identity | None:
        self.get_calls.append(external_id)
        if self.fail_reads:
            raise IdentityClientError("fake get failed")
        if self.missing_reads:
            return None
        return self.identities.get(external_id)

    def get_identity_by_email(self, email: str) -> Identity | None:
        self.get_by_email_calls.append(email)
        if self.fail_reads:
            raise IdentityClientError("fake get-by-email failed")
        if self.missing_reads:
            return None
        needle = email.lower()
        for identity in self.identities.values():
            if identity.email.lower() == needle:
                return identity
        return None

    def _email_owner(
        self, email: str, *, except_id: str | None = None
    ) -> Identity | None:
        needle = email.lower()
        for identity in self.identities.values():
            if identity.email.lower() != needle:
                continue
            if except_id is not None and identity.external_id == except_id:
                continue
            return identity
        return None

    def _store(self, payload: IdentityUpsert) -> Identity:
        owner = self._email_owner(payload.email, except_id=payload.external_id)
        if owner is not None:
            raise IdentityClientError(
                "http 409",
                status_code=409,
                error="conflict",
            )
        existing = self.identities.get(payload.external_id)
        now = format_created_at(datetime.now(UTC))
        identity = Identity(
            id=existing.id
            if existing
            else f"usr_idp_{payload.external_id[4:12]}",
            external_id=payload.external_id,
            email=payload.email,
            name=payload.name,
            admin=payload.admin,
            credential_present=True,
            created_at=(
                existing.created_at if existing else payload.created_at
            ),
            updated_at=now,
        )
        self.identities[payload.external_id] = identity
        self.hashes[payload.external_id] = payload.hashed_password
        return identity

    def _raise_if_credential_store_down(self) -> None:
        if self.credential_store_failures_remaining <= 0:
            return
        self.credential_store_failures_remaining -= 1
        raise IdentityClientError(
            "http 502 error=credential_store_unavailable",
            status_code=502,
            error="credential_store_unavailable",
        )
