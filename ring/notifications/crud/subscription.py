from __future__ import annotations

from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
from ring.notifications.models.subscription import Subscription
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.parties.models.user_model import User


def create_subscription(
    db: Session, subscription: SubscriptionCreate
) -> Subscription:
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
    db_user = get_model(db, User, user_api_identifier)
    return db_user.notification_subscriptions
