"""CRUD operations for comment management.

This module provides functions for managing comments in the database, including
creation, retrieval, updates, and soft deletion operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

from ring.api_identifier import util as api_identifier_crud
from ring.letters.models.comment_model import Comment
from ring.letters.models.question_model import Question
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_comment(
    db: Session,
    question: Question,
    author: User,
    content: str,
) -> Comment:
    """Create a new comment on a question.

    Args:
        db (Session): Database session
        question (Question): Question being commented on
        author (User): User creating the comment
        content (str): Text content of the comment

    Returns:
        Comment: Created comment instance
    """
    comment = Comment.create(
        question=question,
        author=author,
        content=content,
    )
    db.add(comment)
    return comment


def get_comment(
    db: Session,
    comment_api_id: str,
    include_deleted: bool = False,
) -> Optional[Comment]:
    """Get a comment by its API identifier.

    Args:
        db (Session): Database session
        comment_api_id (str): API identifier of the comment
        include_deleted (bool): Whether to include soft-deleted comments

    Returns:
        Optional[Comment]: Comment instance or None if not found
    """
    query = db.query(Comment).filter(Comment.api_identifier == comment_api_id)
    
    if not include_deleted:
        query = query.filter(Comment.deleted_at.is_(None))
    
    return query.first()


def get_comments_for_question(
    db: Session,
    question_api_id: str,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[Sequence[Comment], int]:
    """Get all comments for a specific question with pagination.

    Args:
        db (Session): Database session
        question_api_id (str): API identifier of the question
        include_deleted (bool): Whether to include soft-deleted comments
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return

    Returns:
        tuple[Sequence[Comment], int]: List of comments and total count
    """
    # Get the question
    question = api_identifier_crud.get_model(db, Question, question_api_id)
    
    # Base query with author and question loaded
    query = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .options(joinedload(Comment.question))
        .filter(Comment.question_id == question.id)
    )
    
    # Filter out deleted comments unless requested
    if not include_deleted:
        query = query.filter(Comment.deleted_at.is_(None))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
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
        db (Session): Database session
        comment (Comment): Comment to update
        content (str): New content for the comment

    Returns:
        Comment: Updated comment instance
    """
    comment.content = content
    comment.updated_at = datetime.now()
    return comment


def soft_delete_comment(
    db: Session,
    comment: Comment,
    deleted_by: User,
) -> Comment:
    """Soft delete a comment.

    Args:
        db (Session): Database session
        comment (Comment): Comment to delete
        deleted_by (User): User who is deleting the comment (usually admin)

    Returns:
        Comment: Deleted comment instance
    """
    comment.deleted_at = datetime.now()
    comment.deleted_by = deleted_by
    return comment


def can_user_edit_comment(user: User, comment: Comment) -> bool:
    """Check if a user can edit a comment.

    Args:
        user (User): User attempting to edit
        comment (Comment): Comment to be edited

    Returns:
        bool: True if user can edit, False otherwise
    """
    # User can edit their own non-deleted comments
    return (
        comment.author_id == user.id 
        and comment.deleted_at is None
    )


def can_user_delete_comment(user: User, comment: Comment) -> bool:
    """Check if a user can delete a comment.

    Args:
        user (User): User attempting to delete
        comment (Comment): Comment to be deleted

    Returns:
        bool: True if user can delete, False otherwise
    """
    # Only admins can delete comments (soft delete)
    return user.admin


