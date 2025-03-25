from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
from ring.notifications.models.subscription import Subscription
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.parties.models.user_model import User


def create_subscription(
    db: Session, subscription: SubscriptionCreate
) -> Subscription:
    """Create a new web push notification subscription.

    :param db: Database session
    :type db: Session
    :param subscription: Subscription creation data
    :type subscription: SubscriptionCreate
    :return: Newly created subscription
    :rtype: Subscription
    :raises IDNotFoundException: If user with given API ID is not found
    """
    db_user = get_model(db, User, subscription.user_api_identifier)
    db_subscription = Subscription.create(
        endpoint=subscription.endpoint,
        keys=subscription.keys,
        user=db_user,
    )
    db.add(db_subscription)
    return db_subscription


def get_subscriptions_for_user(
    db: Session, user_api_identifier: str
) -> list[Subscription]:
    """Get all push notification subscriptions for a user.

    :param db: Database session
    :type db: Session
    :param user_api_identifier: API identifier of the user
    :type user_api_identifier: str
    :return: List of user's subscriptions
    :rtype: list[Subscription]
    :raises IDNotFoundException: If user with given API ID is not found
    """
    db_user = get_model(db, User, user_api_identifier)
    return db_user.notification_subscriptions


def get_subscription_by_endpoint(
    db: Session, endpoint: str
) -> Subscription | None:
    """Find a subscription by its endpoint URL.

    :param db: Database session
    :type db: Session
    :param endpoint: Push notification endpoint URL
    :type endpoint: str
    :return: Found subscription or None
    :rtype: Subscription | None
    """
    return db.scalars(
        select(Subscription).where(Subscription.endpoint == endpoint)
    ).one_or_none()


def serialize_subscription_info(
    db_subscription: Subscription,
) -> dict[str, str]:
    """Convert a subscription to the format required by pywebpush.

    :param db_subscription: Subscription to serialize
    :type db_subscription: Subscription
    :return: Dictionary with endpoint and keys formatted for web push
    :rtype: dict[str, str]
    """
    return {
        "endpoint": db_subscription.endpoint,
        "keys": {
            "p256dh": db_subscription.keys.get("p256dh", ""),
            "auth": db_subscription.keys.get("auth", ""),
        },
    }  # type: ignore
