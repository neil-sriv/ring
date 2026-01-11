"""SQLAlchemy model for comment management.

This module defines the Comment model, which represents user comments on any
API-identified object in the system. Comments use a weak reference pattern,
storing just the api_identifier of the target object rather than a foreign key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.linked_schemas import CommentLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.user_model import User


@register_api_class(APIPrefix.COMMENT)
class Comment(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a comment on any API-identified object.

    Comments use a weak reference pattern - they store the api_identifier of
    the target object rather than a foreign key. This allows comments to be
    attached to any model in the system without requiring schema changes.

    Attributes:
        id: Primary key identifier
        api_identifier: Unique API identifier for the comment
        content: Text content of the comment
        target_api_id: API identifier of the object being commented on
        author: User who wrote the comment
    """

    __tablename__ = "comment"

    API_ID_PREFIX = APIPrefix.COMMENT
    PYDANTIC_MODEL = CommentLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    content: Mapped[str] = mapped_column(Text)

    # Weak reference to the target object (stores api_identifier)
    target_api_id: Mapped[str] = mapped_column(String, index=True)

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    author: Mapped["User"] = relationship(foreign_keys=[author_id])

    def __init__(
        self,
        target_api_id: str,
        author: User,
        content: str,
    ) -> None:
        """Initialize a new Comment instance.

        Args:
            target_api_id: API identifier of the object being commented on
            author: User creating the comment
            content: Text content of the comment
        """
        APIIdentified.__init__(self)
        self.target_api_id = target_api_id
        self.author = author
        self.content = content

    @classmethod
    def create(
        cls,
        target_api_id: str,
        author: User,
        content: str,
    ) -> Comment:
        """Create a new Comment instance.

        Factory method to create a new comment with the given parameters.

        Args:
            target_api_id: API identifier of the object being commented on
            author: User creating the comment
            content: Text content of the comment

        Returns:
            Comment: New Comment instance
        """
        return cls(target_api_id, author, content)
