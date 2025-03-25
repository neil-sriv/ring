"""VAPID-based web push notification sending functionality.

This module provides functions for sending web push notifications using VAPID
(Voluntary Application Server Identification) authentication.
"""

import json

from pywebpush import WebPushException, webpush  # type: ignore

from ring.config import get_config
from ring.lib.logger import logger
from ring.notifications.crud.subscription import serialize_subscription_info
from ring.notifications.models.subscription import Subscription
from ring.parties.models.user_model import User


def send_push_notification(
    subscription_info: Subscription, payload: dict[str, str]
) -> None:
    """Send a web push notification to a specific subscription.

    :param subscription_info: Subscription to send notification to
    :type subscription_info: Subscription
    :param payload: Data to send in the notification
    :type payload: dict[str, str]
    :raises WebPushException: If sending the notification fails
    """
    try:
        # Perform web push
        response = webpush(
            subscription_info=serialize_subscription_info(subscription_info),  # type: ignore
            data=json.dumps(payload),
            vapid_private_key=get_config().VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:neilsriv.cs+vapid@gmail.com"},
        )
        logger.info(f"Push notification sent successfully: {response}")
    except WebPushException as e:
        logger.error(f"Error sending push notification: {e}")


def send_push_notification_to_user(
    user: User, payload: dict[str, str]
) -> None:
    """Send a web push notification to a user's most recent subscription.

    :param user: User to send notification to
    :type user: User
    :param payload: Data to send in the notification
    :type payload: dict[str, str]
    :raises IndexError: If user has no subscriptions
    """
    newest_subscription = user.notification_subscriptions[-1]
    send_push_notification(newest_subscription, payload)
