"""Tests for the push notification subscription API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.user_factory import UserFactory


class TestSubscriptionApi:
    """Test suite for notification subscription API endpoints."""

    def test_post_subscription_for_self(
        self,
        authenticated_client: TestClient,
        current_user: User,
    ):
        """Authenticated users can register a push subscription for themselves."""
        response = authenticated_client.post(
            "/notifications/subscription",
            json={
                "endpoint": "https://example.com/push/self",
                "keys": {"p256dh": "test-p256dh", "auth": "test-auth"},
                "user_api_identifier": current_user.api_identifier,
            },
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Subscription created"}

    def test_post_subscription_rejects_other_user(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Clients cannot attach a push endpoint to a different user."""
        other_user = UserFactory.create()
        db_session.commit()
        assert other_user.api_identifier != current_user.api_identifier

        for user_api_identifier in (
            other_user.api_identifier,
            "invalid-user",
        ):
            response = authenticated_client.post(
                "/notifications/subscription",
                json={
                    "endpoint": f"https://example.com/push/{user_api_identifier}",
                    "keys": {"p256dh": "test-p256dh", "auth": "test-auth"},
                    "user_api_identifier": user_api_identifier,
                },
            )

            assert response.status_code == 403
            assert response.json() == {
                "detail": "Cannot create a subscription for a different user"
            }

    def test_post_subscription_existing_endpoint(
        self,
        authenticated_client: TestClient,
        current_user: User,
    ):
        """Duplicate endpoints return an existing-subscription message."""
        payload = {
            "endpoint": "https://example.com/push/dup",
            "keys": {"p256dh": "test-p256dh", "auth": "test-auth"},
            "user_api_identifier": current_user.api_identifier,
        }
        first = authenticated_client.post(
            "/notifications/subscription",
            json=payload,
        )
        assert first.status_code == 200
        assert first.json() == {"message": "Subscription created"}

        second = authenticated_client.post(
            "/notifications/subscription",
            json=payload,
        )
        assert second.status_code == 200
        assert second.json() == {"message": "Subscription already exists"}
