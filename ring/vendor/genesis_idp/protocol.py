"""Client interface Ring uses; later extractable as the shared Python client."""

from __future__ import annotations

from typing import Protocol

from .models import Identity, IdentityPatch, IdentityUpsert


class IdentityClient(Protocol):
    """Typed identity-service client.

    Implementations must be sync: dual-sync runs in FastAPI BackgroundTasks
    and in CLI scripts, not on the request event loop.
    """

    def upsert_identity(self, payload: IdentityUpsert) -> Identity:
        """Idempotent PUT. Ring's dual-write call."""
        ...

    def create_identity(self, payload: IdentityUpsert) -> Identity:
        """Create-only POST. 409 if the identity already exists."""
        ...

    def patch_identity(
        self, external_id: str, payload: IdentityPatch
    ) -> Identity:
        """Partial PATCH. ``hashed_password`` is optional."""
        ...

    def get_identity(self, external_id: str) -> Identity | None:
        """GET by Ring ``usr_`` external_id. None if 404."""
        ...

    def get_identity_by_email(self, email: str) -> Identity | None:
        """GET by email. None if 404."""
        ...
