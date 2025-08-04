"""Comment API endpoints.

This module provides FastAPI endpoints for managing comments on questions,
including creating, reading, updating, and deleting comments with proper
permission checks.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ring.api_identifier import util as api_identifier_crud
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud import comment as comment_crud
from ring.letters.models.comment_model import Comment
from ring.letters.models.question_model import Question
from ring.letters.schemas.comment import (
    CommentCreate,
    CommentUpdate,
)
from ring.ring_pydantic.core import ResponseMessage
from ring.ring_pydantic.linked_schemas import CommentLinked
from pydantic import BaseModel, model_validator

router = APIRouter()


class CommentsListResponse(BaseModel):
    """Response schema for paginated comments list."""
    comments: list[CommentLinked]
    total: int
    skip: int
    limit: int
    has_more: bool


@router.post(
    "/questions/{question_api_id}/comments",
    response_model=CommentLinked,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    question_api_id: str,
    comment_data: CommentCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Comment:
    """Create a new comment on a question.

    Only group members can comment on questions within their group's letters.

    Args:
        question_api_id (str): API identifier of the question
        comment_data (CommentCreate): Comment creation data
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Comment: Created comment with author and question information

    Raises:
        PermissionError: If user doesn't have access to the question
    """
    # This checks if user has access to the question (via group membership)
    question = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        question_api_id,
    )
    
    # Create the comment
    comment = comment_crud.create_comment(
        db=req_dep.db,
        question=question,
        author=req_dep.current_user,
        content=comment_data.content,
    )
    
    req_dep.db.commit()
    
    # Refresh to ensure relationships are loaded
    req_dep.db.refresh(comment)
    
    # Convert to Pydantic model
    return CommentLinked.model_validate(comment)


@router.get(
    "/questions/{question_api_id}/comments",
    response_model=CommentsListResponse,
)
async def get_comments(
    question_api_id: str,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum comments to return"),
    include_deleted: bool = Query(False, description="Include deleted comments (admin only)"),
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> dict:
    """Get comments for a question with pagination.

    Args:
        question_api_id (str): API identifier of the question
        skip (int): Number of comments to skip for pagination
        limit (int): Maximum number of comments to return
        include_deleted (bool): Include soft-deleted comments (admin only)
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        dict: Paginated response with comments list and metadata

    Raises:
        PermissionError: If user doesn't have access to the question
        HTTPException: If non-admin tries to view deleted comments
    """
    # Check access to question
    question = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        question_api_id,
    )
    
    # Only admins can see deleted comments
    if include_deleted and not req_dep.current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view deleted comments",
        )
    
    # Get comments with pagination
    comments, total = comment_crud.get_comments_for_question(
        db=req_dep.db,
        question_api_id=question_api_id,
        include_deleted=include_deleted,
        skip=skip,
        limit=limit,
    )
    
    # Convert SQLAlchemy models to Pydantic models
    comment_list = []
    for comment in comments:
        try:
            # Ensure relationships are loaded
            if not comment.author:
                raise ValueError(f"Comment {comment.api_identifier} has no author")
            if not comment.question:
                raise ValueError(f"Comment {comment.api_identifier} has no question")
            
            # Convert to Pydantic model
            comment_data = CommentLinked.model_validate(comment)
            comment_list.append(comment_data)
        except Exception as e:
            # Log the error but continue processing other comments
            print(f"Error serializing comment {comment.api_identifier}: {e}")
            continue
    
    return CommentsListResponse(
        comments=comment_list,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


@router.patch(
    "/comments/{comment_api_id}",
    response_model=CommentLinked,
)
async def update_comment(
    comment_api_id: str,
    comment_data: CommentUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Comment:
    """Update a comment's content.

    Only the comment author can edit their own comments.

    Args:
        comment_api_id (str): API identifier of the comment
        comment_data (CommentUpdate): Updated comment data
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Comment: Updated comment

    Raises:
        PermissionError: If user doesn't have access to the comment
        HTTPException: If user is not the comment author or comment is deleted
    """
    # Load and check access to comment
    comment = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        comment_api_id,
    )
    
    # Check if user can edit
    if not comment_crud.can_user_edit_comment(req_dep.current_user, comment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )
    
    # Update the comment
    updated_comment = comment_crud.update_comment(
        db=req_dep.db,
        comment=comment,
        content=comment_data.content,
    )
    
    req_dep.db.commit()
    
    # Refresh to ensure relationships are loaded
    req_dep.db.refresh(updated_comment)
    
    # Convert to Pydantic model
    return CommentLinked.model_validate(updated_comment)


@router.delete(
    "/comments/{comment_api_id}",
    response_model=ResponseMessage,
)
async def delete_comment(
    comment_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ResponseMessage:
    """Soft delete a comment.

    Only group admins can delete comments. Regular users who want to remove
    their own comments should edit them instead.

    Args:
        comment_api_id (str): API identifier of the comment
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        ResponseMessage: Success message

    Raises:
        PermissionError: If user doesn't have access to the comment
        HTTPException: If user is not an admin
    """
    # Load and check access
    comment = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        comment_api_id,
    )
    
    # Check if user can delete
    if not comment_crud.can_user_delete_comment(req_dep.current_user, comment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete comments",
        )
    
    # Check if already deleted
    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment is already deleted",
        )
    
    # Soft delete
    comment_crud.soft_delete_comment(
        db=req_dep.db,
        comment=comment,
        deleted_by=req_dep.current_user,
    )
    
    req_dep.db.commit()
    return ResponseMessage(message="Comment deleted successfully")