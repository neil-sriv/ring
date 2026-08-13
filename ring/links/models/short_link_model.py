"""SQLAlchemy model for short links.

A short link is a compact, shareable token that resolves to an existing
API-identified resource. It uses the **weak reference** pattern described in
AGENTS.md: rather than a polymorphic foreign key, it stores the target's
``api_identifier`` in ``target_api_id`` and resolves it with ``bulk_get_models``.
Links are hard-deleted when revoked.
"""

from __future__ import annotations

import secrets
import string
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified, APIPrefix
from ring.api_identifier.util import register_api_class
from ring.created_at import CreatedAtMixin
from ring.links.constants import target_type_for_api_id
from ring.links.schemas.short_link import ShortLink as ShortLinkSchema
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.user_model import User

# URL-safe, unambiguous alphabet for tokens. secrets provides the CSPRNG so
# tokens are non-sequential and hard to guess.
TOKEN_ALPHABET = string.ascii_letters + string.digits
DEFAULT_TOKEN_LENGTH = 8


def generate_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
    """Generate a random, URL-safe short link token.

    Args:
        length (int): Number of characters in the token.

    Returns:
        str: A randomly generated token.
    """
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(length))


@register_api_class(APIPrefix.SHORT_LINK)
class ShortLink(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a short link.

    Attributes:
        id (int): Primary key.
        api_identifier (str): Unique API identifier with the ``shl`` prefix.
        token (str): Short, URL-safe token used in the shareable path.
        target_api_id (str): Weak reference to the shared resource's identifier.
        creator_id (int): Foreign key to the user who created the link.
        creator (User): Relationship to the creating user.
        created_at (datetime): Timestamp of link creation.
    """

    __tablename__ = "short_link"

    API_ID_PREFIX = APIPrefix.SHORT_LINK
    PYDANTIC_MODEL = ShortLinkSchema

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    target_api_id: Mapped[str] = mapped_column(index=True, nullable=False)

    creator_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id", name="short_link_creator_id_fkey", ondelete="CASCADE"
        ),
        index=True,
        nullable=False,
    )
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])

    def __init__(
        self,
        target_api_id: str,
        creator: User,
        token: str | None = None,
    ) -> None:
        """Initialize a new short link.

        Args:
            target_api_id (str): API identifier of the resource to share.
            creator (User): User creating the link.
            token (str | None): Explicit token; a random one is generated when
                omitted.
        """
        APIIdentified.__init__(self)
        self.target_api_id = target_api_id
        self.creator = creator
        self.token = token or generate_token()

    @classmethod
    def create(
        cls,
        target_api_id: str,
        creator: User,
        token: str | None = None,
    ) -> ShortLink:
        """Create a new short link instance.

        Args:
            target_api_id (str): API identifier of the resource to share.
            creator (User): User creating the link.
            token (str | None): Explicit token; a random one is generated when
                omitted.

        Returns:
            ShortLink: New short link instance.
        """
        return cls(target_api_id=target_api_id, creator=creator, token=token)

    @property
    def target_type(self) -> str:
        """Coarse category of the target resource, derived from its prefix."""
        target_type = target_type_for_api_id(self.target_api_id)
        return target_type.value if target_type else ""

    @property
    def path(self) -> str:
        """Relative shareable path for the link (``/s/<token>``)."""
        return f"/s/{self.token}"
