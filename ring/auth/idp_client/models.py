"""Pydantic shapes for the locked identity API (v2, 2026-10-15).

Ring maps ``user.api_identifier`` to ``external_id`` and talks only to the
IdP. ``hashed_password`` is write-only on PUT/POST/PATCH; GET responses
never include it. Dual-read uses ``credential_present``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_encoded_hash(value: str) -> str:
    """Reject plaintext. Encoded hashes start with ``$`` (bcrypt or PHC)."""
    if not value.startswith("$"):
        raise ValueError("hashed_password must start with $")
    return value


class Identity(BaseModel):
    """Identity as returned by GET. Hash is never present."""

    model_config = ConfigDict(extra="ignore")

    id: str
    external_id: str
    email: str
    name: str | None = None
    admin: bool
    credential_present: bool
    created_at: str
    updated_at: str


class IdentityUpsert(BaseModel):
    """Full PUT/POST body. Unknown fields are rejected (400)."""

    model_config = ConfigDict(extra="forbid")

    external_id: str
    email: str
    name: str | None = None
    hashed_password: str = Field(min_length=20, max_length=512)
    admin: bool
    created_at: str

    @field_validator("hashed_password")
    @classmethod
    def hashed_password_must_be_encoded(cls, value: str) -> str:
        return _require_encoded_hash(value)

    def request_body(self) -> dict[str, object]:
        """JSON object for PUT/POST. Includes ``name: null`` when unset."""
        return {
            "external_id": self.external_id,
            "email": self.email,
            "name": self.name,
            "hashed_password": self.hashed_password,
            "admin": self.admin,
            "created_at": self.created_at,
        }


class IdentityPatch(BaseModel):
    """Partial PATCH body. Omitted fields stay. Hash is optional."""

    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    name: str | None = None
    hashed_password: str | None = Field(
        default=None, min_length=20, max_length=512
    )
    admin: bool | None = None

    @field_validator("hashed_password")
    @classmethod
    def hashed_password_must_be_encoded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_encoded_hash(value)

    def request_body(self) -> dict[str, object]:
        """JSON object including only fields the caller set."""
        body: dict[str, object] = {}
        if "email" in self.model_fields_set:
            body["email"] = self.email
        if "name" in self.model_fields_set:
            body["name"] = self.name
        if "hashed_password" in self.model_fields_set:
            body["hashed_password"] = self.hashed_password
        if "admin" in self.model_fields_set:
            body["admin"] = self.admin
        return body
