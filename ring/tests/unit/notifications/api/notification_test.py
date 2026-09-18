"""Tests for the notification API endpoints.

This module tests listing, unread counts, read/unread marking, and deletion
of in-app notifications, including authorization boundaries between users.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.notifications.constants import NotificationType
from ring.parties.models.user_model import User
from ring.tests.factories.notifications.notification_factory import (
    NotificationFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestNotificationApi:
    """Test suite for notification API endpoints."""

    def test_list_empty(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        response = authenticated_client.get("/notifications/")
        assert response.status_code == 200
        assert response.json() == {
            "notifications": [],
            "unread_count": 0,
            "total_count": 0,
        }

    def test_list_returns_only_own_notifications(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        mine = NotificationFactory.create(
            recipient=current_user,
            type=NotificationType.LETTER_SENT,
            title="A new letter",
            body="Ring Newsletter #1 is here",
            target_api_id="lttr_abc",
        )
        NotificationFactory.create(recipient=UserFactory.create())
        db_session.commit()

        response = authenticated_client.get("/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["unread_count"] == 1
        assert len(data["notifications"]) == 1
        notification = data["notifications"][0]
        assert notification["api_identifier"] == mine.api_identifier
        assert notification["type"] == "letter_sent"
        assert notification["title"] == "A new letter"
        assert notification["body"] == "Ring Newsletter #1 is here"
        assert notification["target_api_id"] == "lttr_abc"
        assert notification["read_at"] is None

    def test_list_unread_only_and_pagination(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        notifications = [
            NotificationFactory.create(recipient=current_user)
            for _ in range(3)
        ]
        db_session.commit()
        read_response = authenticated_client.post(
            f"/notifications/{notifications[0].api_identifier}:read"
        )
        assert read_response.status_code == 200

        response = authenticated_client.get(
            "/notifications/", params={"unread_only": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 2
        assert data["total_count"] == 3
        assert {n["api_identifier"] for n in data["notifications"]} == {
            notifications[1].api_identifier,
            notifications[2].api_identifier,
        }

        paged = authenticated_client.get(
            "/notifications/", params={"limit": 1, "offset": 1}
        )
        assert paged.status_code == 200
        assert len(paged.json()["notifications"]) == 1

    def test_unread_count(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        NotificationFactory.create(recipient=current_user)
        NotificationFactory.create(recipient=current_user)
        NotificationFactory.create(recipient=UserFactory.create())
        db_session.commit()

        response = authenticated_client.get("/notifications/unread-count")
        assert response.status_code == 200
        assert response.json() == {"unread_count": 2}

    def test_mark_read_and_unread(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        notification = NotificationFactory.create(recipient=current_user)
        db_session.commit()

        read_response = authenticated_client.post(
            f"/notifications/{notification.api_identifier}:read"
        )
        assert read_response.status_code == 200
        assert read_response.json()["read_at"] is not None

        unread_response = authenticated_client.post(
            f"/notifications/{notification.api_identifier}:unread"
        )
        assert unread_response.status_code == 200
        assert unread_response.json()["read_at"] is None

    def test_mark_read_other_users_notification_forbidden(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        other_notification = NotificationFactory.create(
            recipient=UserFactory.create()
        )
        db_session.commit()

        response = authenticated_client.post(
            f"/notifications/{other_notification.api_identifier}:read"
        )
        assert response.status_code == 403
        db_session.refresh(other_notification)
        assert other_notification.read_at is None

    def test_mark_read_missing_notification_forbidden(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        response = authenticated_client.post(
            "/notifications/notif_00000000-0000-0000-0000-000000000000:read"
        )
        assert response.status_code == 403

    def test_read_all(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        for _ in range(3):
            NotificationFactory.create(recipient=current_user)
        other_notification = NotificationFactory.create(
            recipient=UserFactory.create()
        )
        db_session.commit()

        response = authenticated_client.post("/notifications/read-all")
        assert response.status_code == 200
        assert response.json() == {"unread_count": 0}

        listed = authenticated_client.get("/notifications/")
        assert listed.json()["unread_count"] == 0
        assert listed.json()["total_count"] == 3
        db_session.refresh(other_notification)
        assert other_notification.read_at is None

    def test_delete_notification(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        notification = NotificationFactory.create(recipient=current_user)
        db_session.commit()

        response = authenticated_client.delete(
            f"/notifications/{notification.api_identifier}"
        )
        assert response.status_code == 200

        listed = authenticated_client.get("/notifications/")
        assert listed.json()["total_count"] == 0

    def test_delete_other_users_notification_forbidden(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        other_notification = NotificationFactory.create(
            recipient=UserFactory.create()
        )
        db_session.commit()

        response = authenticated_client.delete(
            f"/notifications/{other_notification.api_identifier}"
        )
        assert response.status_code == 403
