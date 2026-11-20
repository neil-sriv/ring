"""Tests for push subscription CRUD."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.notifications.crud.subscription import create_subscription
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.tests.factories.parties.user_factory import UserFactory


def test_create_subscription_uses_caller_not_body_id(
    db_session: Session,
) -> None:
    """The body user id is ignored. The passed-in user owns the row."""
    caller = UserFactory.create()
    other = UserFactory.create()
    db_session.commit()

    created = create_subscription(
        db_session,
        SubscriptionCreate(
            endpoint="https://example.com/push/crud",
            keys={"p256dh": "test-p256dh", "auth": "test-auth"},
            user_api_identifier=other.api_identifier,
        ),
        caller,
    )
    db_session.flush()

    assert created.user_id == caller.id
    assert created.user_id != other.id
