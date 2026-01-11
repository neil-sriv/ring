"""Comment API endpoints.

This module provides FastAPI endpoints for managing comments on any API-identified
object, including creating, reading, updating, and deleting comments with proper
permission checks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ring.api_identifier import util as api_identifier_crud
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud import comment as comment_crud
from ring.letters.models.comment_model import Comment
from ring.letters.schemas.comment import (
    CommentCreate,
    CommentUnlinked,
    CommentUpdate,
)
from ring.ring_pydantic.core import ResponseMessage
from ring.ring_pydantic.linked_schemas import CommentLinked

router = APIRouter()


class CommentsListResponse(BaseModel):
    """Response schema for paginated comments list."""

    comments: list[CommentLinked]
    total: int
    skip: int
    limit: int
    has_more: bool


@router.post(
    "/comments/{target_api_id}",
    response_model=CommentLinked,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    target_api_id: str,
    comment_data: CommentCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> CommentLinked:
    """Create a new comment on any API-identified object.

    The user must have read access to the target object to comment on it.

    Args:
        target_api_id: API identifier of the object to comment on
        comment_data: Comment creation data
        req_dep: Request dependencies

    Returns:
        Created comment with author information

    Raises:
        PermissionError: If user doesn't have access to the target object
    """
    # Check if user has access to the target object
    load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        target_api_id,
    )

    # Create the comment
    comment = comment_crud.create_comment(
        db=req_dep.db,
        target_api_id=target_api_id,
        author=req_dep.current_user,
        content=comment_data.content,
    )

    req_dep.db.commit()
    req_dep.db.refresh(comment)

    return CommentLinked(
        api_identifier=comment.api_identifier,
        content=comment.content,
        created_at=comment.created_at,
        target_api_id=comment.target_api_id,
        author_api_identifier=comment.author.api_identifier,
        author=comment.author,
    )


@router.get(
    "/comments/{target_api_id}",
    response_model=CommentsListResponse,
)
async def get_comments(
    target_api_id: str,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum comments to return"
    ),
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> CommentsListResponse:
    """Get comments for any API-identified object with pagination.

    Args:
        target_api_id: API identifier of the target object
        skip: Number of comments to skip for pagination
        limit: Maximum number of comments to return
        req_dep: Request dependencies

    Returns:
        Paginated response with comments list and metadata

    Raises:
        PermissionError: If user doesn't have access to the target object
    """
    # Check access to target object
    load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        target_api_id,
    )

    # Get comments with pagination
    comments, total = comment_crud.get_comments_for_target(
        db=req_dep.db,
        target_api_id=target_api_id,
        skip=skip,
        limit=limit,
    )

    # Convert to response models
    comment_list = [
        CommentLinked(
            api_identifier=c.api_identifier,
            content=c.content,
            created_at=c.created_at,
            target_api_id=c.target_api_id,
            author_api_identifier=c.author.api_identifier,
            author=c.author,
        )
        for c in comments
    ]

    return CommentsListResponse(
        comments=comment_list,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


@router.patch(
    "/comments/{comment_api_id}/edit",
    response_model=CommentLinked,
)
async def update_comment(
    comment_api_id: str,
    comment_data: CommentUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> CommentLinked:
    """Update a comment's content.

    Only the comment author can edit their own comments.

    Args:
        comment_api_id: API identifier of the comment
        comment_data: Updated comment data
        req_dep: Request dependencies

    Returns:
        Updated comment

    Raises:
        PermissionError: If user doesn't have access to the comment
        HTTPException: If user is not the comment author
    """
    # Load comment
    comment = comment_crud.get_comment(req_dep.db, comment_api_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
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
    req_dep.db.refresh(updated_comment)

    return CommentLinked(
        api_identifier=updated_comment.api_identifier,
        content=updated_comment.content,
        created_at=updated_comment.created_at,
        target_api_id=updated_comment.target_api_id,
        author_api_identifier=updated_comment.author.api_identifier,
        author=updated_comment.author,
    )


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
    """Delete a comment.

    Users can delete their own comments. Admins can delete any comment.

    Args:
        comment_api_id: API identifier of the comment
        req_dep: Request dependencies

    Returns:
        Success message

    Raises:
        HTTPException: If comment not found or user lacks permission
    """
    # Load comment
    comment = comment_crud.get_comment(req_dep.db, comment_api_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Check if user can delete
    if not comment_crud.can_user_delete_comment(req_dep.current_user, comment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    # Delete the comment
    comment_crud.delete_comment(
        db=req_dep.db,
        comment=comment,
    )

    req_dep.db.commit()
    return ResponseMessage(message="Comment deleted successfully")
