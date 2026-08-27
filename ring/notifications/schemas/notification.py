"""Pydantic schemas for in-app notifications.

This module provides Pydantic models for validating and serializing in-app
notification data.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.notifications.constants import NotificationType


class NotificationBase(BaseModel):
    """Base schema for in-app notifications.

    Attributes:
        type (NotificationType): Product event this notification represents
        title (str): Short headline shown in the notification list
        body (str): Supporting copy with event details
        target_api_id (str | None): API identifier of the entity the
            notification points at (e.g. a letter or group), if any
    """

    type: NotificationType
    title: str
    body: str
    target_api_id: str | None = None


class Notification(NotificationBase):
    """Schema representing a notification in the system.

    Attributes:
        api_identifier (str): Unique API identifier with 'notif' prefix
        created_at (AwareDatetime): Timestamp of notification creation
        read_at (AwareDatetime | None): When the recipient read the
            notification, or null while unread
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime
    read_at: AwareDatetime | None = None


class NotificationUnlinked(Notification):
    """Schema for notifications without linked relationships.

    Inherits all fields from Notification but excludes relationship data.
    """

    pass


class NotificationList(BaseModel):
    """Response schema for the notification list endpoint.

    Attributes:
        notifications (list[Notification]): Page of notifications,
            newest first
        unread_count (int): Total unread notifications for the user
        total_count (int): Total notifications for the user
    """

    notifications: list[Notification]
    unread_count: int
    total_count: int


class NotificationUnreadCount(BaseModel):
    """Response schema for the unread-count endpoint.

    Attributes:
        unread_count (int): Total unread notifications for the user
    """

    unread_count: int
