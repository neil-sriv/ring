"""Default identity-service HTTP paths.

Override via ``IdentityClientConfig`` / Ring env when genesis locks a
different prefix. ``{external_id}`` is substituted with Ring's ``usr_`` id.
"""

from __future__ import annotations

DEFAULT_IDENTITY_PATH = "/api/v1/identities/{external_id}"
DEFAULT_COLLECTION_PATH = "/api/v1/identities"
