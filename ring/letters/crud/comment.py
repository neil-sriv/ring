"""CRUD operations for comment management.

This module provides functions for managing comments in the database, including
creation, retrieval, and update operations. Comments use a weak reference pattern
and can be attached to any API-identified object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from sqlalchemy.orm import joinedload

from ring.letters.models.comment_model import Comment
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_comment(
    db: Session,
    target_api_id: str,
    author: User,
    content: str,
) -> Comment:
    """Create a new comment on any API-identified object.

    Args:
        db: Database session
        target_api_id: API identifier of the object being commented on
        author: User creating the comment
        content: Text content of the comment

    Returns:
        Comment: Created comment instance
    """
    comment = Comment.create(
        target_api_id=target_api_id,
        author=author,
        content=content,
    )
    db.add(comment)
    return comment


def get_comment(
    db: Session,
    comment_api_id: str,
) -> Comment | None:
    """Get a comment by its API identifier.

    Args:
        db: Database session
        comment_api_id: API identifier of the comment

    Returns:
        Comment or None if not found
    """
    return (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.api_identifier == comment_api_id)
        .first()
    )


def get_comments_for_target(
    db: Session,
    target_api_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[Sequence[Comment], int]:
    """Get all comments for a specific target object with pagination.

    Args:
        db: Database session
        target_api_id: API identifier of the target object
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (list of comments, total count)
    """
    # Base query with author loaded
    query = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.target_api_id == target_api_id)
    )

    # Get total count
    total = query.count()

    # Apply pagination and ordering (newest first)
    comments = (
        query.order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return comments, total


def update_comment(
    db: Session,
    comment: Comment,
    content: str,
) -> Comment:
    """Update a comment's content.

    Args:
        db: Database session
        comment: Comment to update
        content: New content for the comment

    Returns:
        Comment: Updated comment instance
    """
    comment.content = content
    return comment


def delete_comment(
    db: Session,
    comment: Comment,
) -> None:
    """Delete a comment permanently.

    Args:
        db: Database session
        comment: Comment to delete
    """
    db.delete(comment)


def can_user_edit_comment(user: User, comment: Comment) -> bool:
    """Check if a user can edit a comment.

    Users can only edit their own comments.

    Args:
        user: User attempting to edit
        comment: Comment to be edited

    Returns:
        True if user can edit, False otherwise
    """
    return comment.author_id == user.id


def can_user_delete_comment(user: User, comment: Comment) -> bool:
    """Check if a user can delete a comment.

    Users can delete their own comments, or admins can delete any comment.

    Args:
        user: User attempting to delete
        comment: Comment to be deleted

    Returns:
        True if user can delete, False otherwise
    """
    return comment.author_id == user.id or user.admin
