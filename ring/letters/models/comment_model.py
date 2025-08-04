"""SQLAlchemy model for comment management.

This module defines the Comment model, which represents user comments on questions
within letters. Comments allow group members to discuss the collective responses
to a question.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.linked_schemas import CommentLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.question_model import Question
    from ring.parties.models.user_model import User


@register_api_class(APIPrefix.COMMENT)
class Comment(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a comment on a question.

    A comment is created when a group member wants to discuss the collective
    responses to a question. Comments are displayed below all responses.

    Attributes:
        id (Mapped[int]): Primary key identifier
        api_identifier (Mapped[str]): Unique API identifier for the comment
        content (Mapped[str]): Text content of the comment
        updated_at (Mapped[datetime | None]): Last update timestamp
        deleted_at (Mapped[datetime | None]): Soft delete timestamp
        question (Mapped[Question]): Question being commented on
        author (Mapped[User]): User who wrote the comment
        deleted_by (Mapped[User | None]): Admin who deleted the comment (if deleted)
    """

    __tablename__ = "comment"

    API_ID_PREFIX = APIPrefix.COMMENT
    PYDANTIC_MODEL = CommentLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id"), index=True
    )
    question: Mapped["Question"] = relationship(back_populates="comments")

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    author: Mapped["User"] = relationship(foreign_keys=[author_id])

    deleted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"), nullable=True
    )
    deleted_by: Mapped["User | None"] = relationship(
        foreign_keys=[deleted_by_id]
    )

    def __init__(
        self,
        question: Question,
        author: User,
        content: str,
    ) -> None:
        """Initialize a new Comment instance.

        Args:
            question (Question): Question being commented on
            author (User): User creating the comment
            content (str): Text content of the comment
        """
        APIIdentified.__init__(self)
        self.question = question
        self.author = author
        self.content = content

    @classmethod
    def create(
        cls,
        question: Question,
        author: User,
        content: str,
    ) -> Comment:
        """Create a new Comment instance.

        Factory method to create a new comment with the given parameters.

        Args:
            question (Question): Question being commented on
            author (User): User creating the comment
            content (str): Text content of the comment

        Returns:
            Comment: New Comment instance
        """
        return cls(question, author, content)

    @property
    def is_deleted(self) -> bool:
        """Check if the comment has been soft deleted.

        Returns:
            bool: True if comment has been deleted, False otherwise
        """
        return self.deleted_at is not None
