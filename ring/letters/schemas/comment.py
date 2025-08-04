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
        content (str): The text content of the comment
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
        content (str): Updated text content of the comment
    """

    content: str = Field(..., min_length=1, max_length=5000)


class CommentUnlinked(CommentBase):
    """Schema for comment without relationships.

    Attributes:
        api_identifier (str): Unique API identifier for the comment
        created_at (datetime): Timestamp when comment was created
        updated_at (Optional[datetime]): Timestamp of last update
        author_api_identifier (str): API identifier of the comment author
        question_api_identifier (str): API identifier of the related question
        is_deleted (bool): Whether the comment has been soft deleted
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    api_identifier: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_api_identifier: str
    question_api_identifier: str
    is_deleted: bool = False

    @classmethod
    def from_orm_with_relations(cls, comment):
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
            updated_at=comment.updated_at,
            author_api_identifier=comment.author.api_identifier,
            question_api_identifier=comment.question.api_identifier,
            is_deleted=comment.is_deleted,
        )


class Comment(CommentUnlinked):
    """Full comment schema including metadata.

    Same as CommentUnlinked but can be extended with additional
    computed fields if needed.
    """

    pass
