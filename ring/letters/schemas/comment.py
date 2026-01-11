"""Comment schemas for API operations.

This module defines Pydantic models for comment-related operations, including
creation, updates, and data transfer between the API and database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    """Base schema for comment-related operations.

    Attributes:
        content: The text content of the comment
    """

    content: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    """Schema for creating a comment.

    Inherits content field from CommentBase.
    """

    pass


class CommentUpdate(BaseModel):
    """Schema for updating a comment.

    Attributes:
        content: Updated text content of the comment
    """

    content: str = Field(..., min_length=1, max_length=5000)


class CommentUnlinked(CommentBase):
    """Schema for comment without relationships.

    Attributes:
        api_identifier: Unique API identifier for the comment
        created_at: Timestamp when comment was created
        target_api_id: API identifier of the object being commented on
        author_api_identifier: API identifier of the comment author
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    api_identifier: str
    created_at: datetime
    target_api_id: str
    author_api_identifier: str

    @classmethod
    def from_orm_with_relations(cls, comment: "Comment") -> "CommentUnlinked":
        """Create CommentUnlinked from ORM model with relationships.

        Args:
            comment: SQLAlchemy Comment model instance

        Returns:
            CommentUnlinked: Pydantic model instance
        """
        return cls(
            api_identifier=comment.api_identifier,
            content=comment.content,
            created_at=comment.created_at,
            target_api_id=comment.target_api_id,
            author_api_identifier=comment.author.api_identifier,
        )


class Comment(CommentUnlinked):
    """Full comment schema including metadata.

    Same as CommentUnlinked but can be extended with additional
    computed fields if needed.
    """

    pass
