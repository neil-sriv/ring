"""Vendored genesis-idp sync client (identity API v2).

See ``VENDORED_FROM`` for the source repo, path, and commit. Recopy with
``ring gen genesis-idp --from <neil/genesis clone>``. Sync client only;
``aio`` is not vendored.
"""

from __future__ import annotations

from .config import IdentityClientConfig
from .errors import IdentityClientError
from .fake import FakeIdentityClient
from .http import HttpIdentityClient
from .models import Identity, IdentityPatch, IdentityUpsert
from .protocol import IdentityClient
from .times import created_at_equal, format_created_at

__all__ = [
    "FakeIdentityClient",
    "HttpIdentityClient",
    "Identity",
    "IdentityClient",
    "IdentityClientConfig",
    "IdentityClientError",
    "IdentityPatch",
    "IdentityUpsert",
    "created_at_equal",
    "format_created_at",
]
