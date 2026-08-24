"""Notification dispatch: fan an event out to in-app rows and web push.

Product code should call :func:`notify_users` instead of creating
``Notification`` rows or invoking web push directly. Dispatch creates one
in-app notification per recipient and then best-effort delivers the same
content over web push; push failures never fail the calling flow.
"""

from __future__ import annotations

from typing import Sequence

from loguru import logger
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIPrefix
from ring.lib.app_links import app_url
from ring.notifications.constants import NotificationType
from ring.notifications.crud.notification import create_notification
from ring.notifications.crud.vapid import send_push_notification
from ring.notifications.models.notification import Notification
from ring.parties.models.user_model import User

# App routes for entities a notification can point at. Prefixes without an
# entry fall back to the app root.
_TARGET_PATHS: dict[str, str] = {
    APIPrefix.LETTER.value: "loops",
    APIPrefix.GROUP.value: "groups",
    APIPrefix.DOCUMENT.value: "documents",
}


def target_url(target_api_id: str | None) -> str:
    """Build the absolute app URL a notification should open.

    Args:
        target_api_id (str | None): Weak reference to the target entity

    Returns:
        str: Absolute URL into the web app for the target, or the app root
            when the target has no dedicated page
    """
    if target_api_id:
        prefix = target_api_id.split("_", 1)[0]
        path = _TARGET_PATHS.get(prefix)
        if path:
            return app_url(f"{path}/{target_api_id}")
    return app_url("")


def notify_users(
    db: Session,
    recipients: Sequence[User],
    type: NotificationType,
    title: str,
    body: str = "",
    target_api_id: str | None = None,
) -> list[Notification]:
    """Notify users about a product event.

    Creates one in-app notification per recipient (committed by the caller)
    and best-effort pushes the same content to every web push subscription
    each recipient has registered.

    Args:
        db (Session): Database session
        recipients (Sequence[User]): Users to notify
        type (NotificationType): Product event the notification represents
        title (str): Short headline shown in the notification list
        body (str): Supporting copy with event details
        target_api_id (str | None): Weak reference to the entity the
            notification points at

    Returns:
        list[Notification]: The created in-app notifications
    """
    notifications = [
        create_notification(
            db,
            recipient=recipient,
            type=type,
            title=title,
            body=body,
            target_api_id=target_api_id,
        )
        for recipient in recipients
    ]
    payload = {
        "title": title,
        "body": body,
        "url": target_url(target_api_id),
    }
    for recipient in recipients:
        try:
            for subscription in list(recipient.notification_subscriptions):
                gone = send_push_notification(subscription, payload)
                if gone:
                    # The push service says this subscription no longer
                    # exists; drop it so we stop retrying dead endpoints.
                    db.delete(subscription)
        except Exception:
            # Push delivery must never break the triggering flow
            # (letter sends, invites, ...); the in-app row still lands.
            logger.exception(
                f"Failed web push dispatch to user {recipient.api_identifier}"
            )
    if recipients:
        logger.info(
            "Dispatched {} notification to {} user(s)".format(
                type.value, len(recipients)
            )
        )
    return notifications
