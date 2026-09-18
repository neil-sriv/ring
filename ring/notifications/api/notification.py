"""API endpoints for in-app notifications.

This module provides endpoints for listing a user's notifications, tracking
unread counts, and marking notifications read/unread. All endpoints operate
on the authenticated user's own notifications; access to another user's
notifications is rejected by the authz layer.
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, Query

from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.notifications.crud import notification as notification_crud
from ring.notifications.models.notification import Notification
from ring.notifications.schemas.notification import (
    Notification as NotificationSchema,
)
from ring.notifications.schemas.notification import (
    NotificationList,
    NotificationUnreadCount,
)
from ring.ring_pydantic.core import ResponseMessage

router = APIRouter()


@router.get("/", response_model=NotificationList)
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> NotificationList:
    """List the authenticated user's notifications, newest first.

    Args:
        unread_only (bool): Only include unread notifications
        limit (int): Maximum number of notifications to return
        offset (int): Number of notifications to skip
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        NotificationList: Page of notifications plus unread/total counts
    """
    notifications = notification_crud.list_notifications(
        req_dep.db,
        req_dep.current_user,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return NotificationList(
        notifications=[
            NotificationSchema.model_validate(n) for n in notifications
        ],
        unread_count=notification_crud.count_notifications(
            req_dep.db, req_dep.current_user, unread_only=True
        ),
        total_count=notification_crud.count_notifications(
            req_dep.db, req_dep.current_user
        ),
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> NotificationUnreadCount:
    """Get the authenticated user's unread notification count.

    Args:
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        NotificationUnreadCount: Number of unread notifications
    """
    return NotificationUnreadCount(
        unread_count=notification_crud.count_notifications(
            req_dep.db, req_dep.current_user, unread_only=True
        )
    )


@router.post(
    "/{notification_api_id}:read",
    response_model=NotificationSchema,
)
async def mark_notification_read(
    notification_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Notification:
    """Mark one notification as read.

    Args:
        notification_api_id (str): API identifier of the notification
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Notification: The updated notification

    Raises:
        PermissionError: If the notification belongs to another user
    """
    notification = cast(
        Notification,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.WRITE,
            notification_api_id,
        ),
    )
    notification_crud.mark_notification_read(
        req_dep.db, notification, read=True
    )
    req_dep.db.commit()
    return notification


@router.post(
    "/{notification_api_id}:unread",
    response_model=NotificationSchema,
)
async def mark_notification_unread(
    notification_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Notification:
    """Mark one notification as unread.

    Args:
        notification_api_id (str): API identifier of the notification
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Notification: The updated notification

    Raises:
        PermissionError: If the notification belongs to another user
    """
    notification = cast(
        Notification,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.WRITE,
            notification_api_id,
        ),
    )
    notification_crud.mark_notification_read(
        req_dep.db, notification, read=False
    )
    req_dep.db.commit()
    return notification


@router.post("/read-all", response_model=NotificationUnreadCount)
async def mark_all_notifications_read(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> NotificationUnreadCount:
    """Mark all of the authenticated user's notifications as read.

    Args:
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        NotificationUnreadCount: Unread count after the update (always 0)
    """
    notification_crud.mark_all_notifications_read(
        req_dep.db, req_dep.current_user
    )
    req_dep.db.commit()
    return NotificationUnreadCount(unread_count=0)


@router.delete(
    "/{notification_api_id}",
    response_model=ResponseMessage,
)
async def delete_notification(
    notification_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ResponseMessage:
    """Delete one notification.

    Args:
        notification_api_id (str): API identifier of the notification
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        ResponseMessage: Confirmation message

    Raises:
        PermissionError: If the notification belongs to another user
    """
    notification = cast(
        Notification,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.WRITE,
            notification_api_id,
        ),
    )
    notification_crud.delete_notification(req_dep.db, notification)
    req_dep.db.commit()
    return ResponseMessage(message="Notification deleted")
