"""VAPID-based web push notification sending functionality.

This module provides functions for sending web push notifications using VAPID
(Voluntary Application Server Identification) authentication.
"""

from __future__ import annotations

import json

from loguru import logger
from pywebpush import WebPushException, webpush  # type: ignore

from ring.fastapp.config import get_config
from ring.notifications.crud.subscription import serialize_subscription_info
from ring.notifications.models.subscription import Subscription

# Push service status codes meaning the subscription no longer exists and
# should be pruned (https://datatracker.ietf.org/doc/html/rfc8030#section-5).
SUBSCRIPTION_GONE_STATUS_CODES = frozenset({404, 410})


def send_push_notification(
    subscription_info: Subscription, payload: dict[str, str]
) -> bool:
    """Send a web push notification to a specific subscription.

    Args:
        subscription_info (Subscription): Subscription to send notification to
        payload (dict[str, str]): Data to send in the notification

    Returns:
        bool: True when the push service reported the subscription is gone
            (expired or unsubscribed) and the row should be pruned
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
        if (
            e.response is not None
            and e.response.status_code in SUBSCRIPTION_GONE_STATUS_CODES
        ):
            logger.info(
                "Push subscription {} is gone ({}); pruning".format(
                    subscription_info.api_identifier, e.response.status_code
                )
            )
            return True
        logger.error(f"Error sending push notification: {e}")
    return False
