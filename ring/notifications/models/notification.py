"""In-app notification model.

This module provides the SQLAlchemy model for user-facing in-app
notifications. Each row targets a single recipient and optionally points at
another entity (letter, group, ...) through a weak ``target_api_id``
reference, so any addressable entity can be linked without polymorphic
foreign keys.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.notifications.constants import NotificationType
from ring.notifications.schemas.notification import NotificationUnlinked
from ring.parties.models.user_model import User
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


@register_api_class(APIPrefix.NOTIFICATION)
class Notification(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model for in-app notifications.

    Attributes:
        id (int): Primary key
        api_identifier (str): Unique API identifier with 'notif' prefix
        type (str): NotificationType value for the triggering event
        title (str): Short headline shown in the notification list
        body (str): Supporting copy with event details
        target_api_id (str | None): Weak reference to the entity the
            notification points at (e.g. ``lttr_*`` or ``grp_*``)
        read_at (datetime | None): When the recipient read the notification
        recipient_id (int): Foreign key to the recipient user
        recipient (User): Relationship to the recipient user
        created_at (datetime): Timestamp of notification creation
    """

    __tablename__ = "notification"

    API_ID_PREFIX = APIPrefix.NOTIFICATION
    PYDANTIC_MODEL = NotificationUnlinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(index=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    target_api_id: Mapped[str | None] = mapped_column(
        index=True,
        nullable=True,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id",
            name="notification_recipient_id_fkey",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
    )

    def __init__(
        self,
        recipient: User,
        type: NotificationType,
        title: str,
        body: str = "",
        target_api_id: str | None = None,
    ) -> None:
        """Initialize a new notification.

        Args:
            recipient (User): User the notification is for
            type (NotificationType): Product event this notification represents
            title (str): Short headline shown in the notification list
            body (str): Supporting copy with event details
            target_api_id (str | None): Weak reference to the entity the
                notification points at
        """
        APIIdentified.__init__(self)
        self.recipient = recipient
        self.type = type
        self.title = title
        self.body = body
        self.target_api_id = target_api_id

    @classmethod
    def create(
        cls,
        recipient: User,
        type: NotificationType,
        title: str,
        body: str = "",
        target_api_id: str | None = None,
    ) -> Notification:
        """Create a new notification instance.

        Args:
            recipient (User): User the notification is for
            type (NotificationType): Product event this notification represents
            title (str): Short headline shown in the notification list
            body (str): Supporting copy with event details
            target_api_id (str | None): Weak reference to the entity the
                notification points at

        Returns:
            Notification: New notification instance
        """
        return cls(recipient, type, title, body, target_api_id)
