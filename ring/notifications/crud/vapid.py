"""VAPID-based web push notification sending functionality.

This module provides functions for sending web push notifications using VAPID
(Voluntary Application Server Identification) authentication.
"""

from __future__ import annotations

import json

from loguru import logger
from pywebpush import webpush  # type: ignore

from ring.fastapp.config import get_config
from ring.notifications.crud.subscription import serialize_subscription_info
from ring.parties.models.user_model import User

# Push services normally answer in well under a second. Cap the request so
# a hung endpoint cannot block the caller indefinitely.
PUSH_REQUEST_TIMEOUT_SECONDS = 10.0


def send_push_notification(
    subscription_info: dict[str, str], payload: dict[str, str]
) -> None:
    """Send a web push notification to one subscription.

    Failures, including timeouts, propagate. The caller logs them.

    Args:
        subscription_info (dict[str, str]): pywebpush subscription dict
        payload (dict[str, str]): Data to send in the notification
    """
    response = webpush(
        subscription_info=subscription_info,  # type: ignore
        data=json.dumps(payload),
        vapid_private_key=get_config().VAPID_PRIVATE_KEY,
        vapid_claims={"sub": "mailto:neilsriv.cs+vapid@gmail.com"},
        timeout=PUSH_REQUEST_TIMEOUT_SECONDS,
    )
    logger.info(f"Push notification sent successfully: {response}")


def send_push_notification_to_user(
    user: User, payload: dict[str, str]
) -> None:
    """Send a web push notification to a user's most recent subscription.

    Args:
        user (User): User to send notification to
        payload (dict[str, str]): Data to send in the notification

    Raises:
        IndexError: If user has no subscriptions
    """
    newest_subscription = user.notification_subscriptions[-1]
    send_push_notification(
        serialize_subscription_info(newest_subscription),
        payload,
    )
