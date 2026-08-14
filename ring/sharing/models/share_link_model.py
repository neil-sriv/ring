"""Capability share link: an unguessable token that unlocks a preview.

A share link is a *capability*: whoever holds the token gets the preview for
exactly the one resource the token is bound to, and nothing else. It grants a
minimal, public-safe subset (title, counts) - never the resource's contents -
so a leaked link exposes little, and it can be revoked with a hard delete.

The parent is stored as a weak reference (`target_api_id`) rather than a
polymorphic FK, per the generic-attachable-entity convention in AGENTS.md, so
one table can front letters, documents, or groups.
"""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.sqlalchemy_base import Base


@register_api_class(APIPrefix.SHARE_LINK)
class ShareLink(Base, APIIdentified, CreatedAtMixin):
    """A revocable, unguessable token that enriches one resource's preview.

    Attributes:
        id (int): Primary key
        api_identifier (str): Unique API identifier with the `shrl` prefix
        token (str): The capability secret that travels in the shared URL
        target_api_id (str): Weak reference to the resource being previewed
        created_by_api_id (str): API id of the member who minted the link
        created_at (datetime): Creation timestamp
    """

    __tablename__ = "share_link"

    API_ID_PREFIX = APIPrefix.SHARE_LINK

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    target_api_id: Mapped[str] = mapped_column(index=True, nullable=False)
    created_by_api_id: Mapped[str] = mapped_column(nullable=False)

    def __init__(
        self,
        token: str,
        target_api_id: str,
        created_by_api_id: str,
    ) -> None:
        """Initialize a new share link.

        Args:
            token (str): The capability secret
            target_api_id (str): API id of the resource being shared
            created_by_api_id (str): API id of the member creating the link
        """
        APIIdentified.__init__(self)
        self.token = token
        self.target_api_id = target_api_id
        self.created_by_api_id = created_by_api_id

    @classmethod
    def create(
        cls,
        token: str,
        target_api_id: str,
        created_by_api_id: str,
    ) -> ShareLink:
        """Create a new share link instance.

        Args:
            token (str): The capability secret
            target_api_id (str): API id of the resource being shared
            created_by_api_id (str): API id of the member creating the link

        Returns:
            ShareLink: New share link instance
        """
        return cls(token, target_api_id, created_by_api_id)
