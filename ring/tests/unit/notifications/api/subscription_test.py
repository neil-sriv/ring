"""Tests for the web push subscription API."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.notifications.crud.subscription import get_subscription_by_endpoint
from ring.parties.models.user_model import User
from ring.tests.factories.parties.user_factory import UserFactory


class TestSubscriptionApi:
    """Test suite for push subscription registration."""

    def test_post_subscription_for_self(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        response = authenticated_client.post(
            "/notifications/subscription",
            json={
                "endpoint": "https://push.example.com/self",
                "keys": {"p256dh": "key", "auth": "auth"},
                "user_api_identifier": current_user.api_identifier,
            },
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Subscription created"}
        subscription = get_subscription_by_endpoint(
            db_session, "https://push.example.com/self"
        )
        assert subscription is not None
        assert subscription.user_id == current_user.id

    def test_post_subscription_for_other_user_forbidden(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        other = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            "/notifications/subscription",
            json={
                "endpoint": "https://push.example.com/other",
                "keys": {"p256dh": "key", "auth": "auth"},
                "user_api_identifier": other.api_identifier,
            },
        )
        assert response.status_code == 403
        assert (
            get_subscription_by_endpoint(
                db_session, "https://push.example.com/other"
            )
            is None
        )
