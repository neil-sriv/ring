from __future__ import annotations

from datetime import UTC, datetime

from ring.vendor.genesis_idp.client import (
    Identity,
    IdentityClientError,
    IdentityUpsert,
    format_created_at,
)


class FakeIdentityClient:
    def __init__(self) -> None:
        self.identities: dict[str, Identity] = {}
        self.hashes: dict[str, str] = {}
        self.upsert_calls: list[IdentityUpsert] = []
        self.get_calls: list[str] = []
        self.fail_upserts: bool = False
        self.fail_reads: bool = False
        self.missing_reads: bool = False

    def upsert_identity(self, payload: IdentityUpsert) -> Identity:
        self.upsert_calls.append(payload)
        if self.fail_upserts:
            raise IdentityClientError("fake upsert failed")
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
            id=(
                existing.id
                if existing is not None
                else f"usr_idp_{payload.external_id[4:12]}"
            ),
            external_id=payload.external_id,
            email=payload.email.strip().lower(),
            name=payload.name,
            admin=payload.admin,
            credential_present=True,
            created_at=(
                existing.created_at if existing is not None else payload.created_at
            ),
            updated_at=now,
        )
        self.identities[payload.external_id] = identity
        self.hashes[payload.external_id] = payload.hashed_password
        return identity

    def get_identity(self, external_id: str) -> Identity | None:
        self.get_calls.append(external_id)
        if self.fail_reads:
            raise IdentityClientError("fake get failed")
        if self.missing_reads:
            return None
        return self.identities.get(external_id)

    def _email_owner(
        self, email: str, *, except_id: str | None = None
    ) -> Identity | None:
        needle = email.strip().lower()
        for identity in self.identities.values():
            if identity.email != needle:
                continue
            if except_id is not None and identity.external_id == except_id:
                continue
            return identity
        return None
