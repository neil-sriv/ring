"""CRUD operations for in-app notifications.

This module provides functions for creating, listing, and updating in-app
notifications in the database. All queries are scoped to a recipient user;
authorization checks live in the API layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ring.notifications.constants import NotificationType
from ring.notifications.models.notification import Notification
from ring.parties.models.user_model import User


def create_notification(
    db: Session,
    recipient: User,
    type: NotificationType,
    title: str,
    body: str = "",
    target_api_id: str | None = None,
) -> Notification:
    """Create a new in-app notification for a user.

    Args:
        db (Session): Database session
        recipient (User): User the notification is for
        type (NotificationType): Product event this notification represents
        title (str): Short headline shown in the notification list
        body (str): Supporting copy with event details
        target_api_id (str | None): Weak reference to the entity the
            notification points at

    Returns:
        Notification: Newly created notification
    """
    db_notification = Notification.create(
        recipient=recipient,
        type=type,
        title=title,
        body=body,
        target_api_id=target_api_id,
    )
    db.add(db_notification)
    return db_notification


def list_notifications(
    db: Session,
    user: User,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Notification]:
    """List a user's notifications, newest first.

    Args:
        db (Session): Database session
        user (User): Recipient whose notifications to list
        unread_only (bool): Only include unread notifications
        limit (int): Maximum number of notifications to return
        offset (int): Number of notifications to skip

    Returns:
        Sequence[Notification]: Page of the user's notifications
    """
    query = (
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    return db.scalars(query).all()


def count_notifications(
    db: Session, user: User, unread_only: bool = False
) -> int:
    """Count a user's notifications.

    Args:
        db (Session): Database session
        user (User): Recipient whose notifications to count
        unread_only (bool): Only count unread notifications

    Returns:
        int: Number of notifications
    """
    query = select(func.count(Notification.id)).where(
        Notification.recipient_id == user.id
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    return db.scalar(query) or 0


def mark_notification_read(
    db: Session, notification: Notification, read: bool = True
) -> Notification:
    """Mark a notification as read or unread.

    Marking an already-read notification as read keeps the original
    ``read_at`` timestamp.

    Args:
        db (Session): Database session
        notification (Notification): Notification to update
        read (bool): True to mark read, False to mark unread

    Returns:
        Notification: The updated notification
    """
    if read and notification.read_at is None:
        notification.read_at = datetime.now(tz=UTC)
    elif not read:
        notification.read_at = None
    return notification


def mark_all_notifications_read(db: Session, user: User) -> int:
    """Mark all of a user's unread notifications as read.

    Args:
        db (Session): Database session
        user (User): Recipient whose notifications to mark read

    Returns:
        int: Number of notifications that were marked read
    """
    result = db.execute(
        update(Notification)
        .where(
            Notification.recipient_id == user.id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(tz=UTC))
    )
    return result.rowcount


def delete_notification(db: Session, notification: Notification) -> None:
    """Hard-delete a notification.

    Args:
        db (Session): Database session
        notification (Notification): Notification to delete
    """
    db.delete(notification)
