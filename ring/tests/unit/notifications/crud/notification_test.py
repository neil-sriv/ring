"""Tests for notification CRUD operations.

This module tests creating, listing, counting, and updating in-app
notifications at the CRUD layer.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.notifications.constants import NotificationType
from ring.notifications.crud.notification import (
    count_notifications,
    create_notification,
    delete_notification,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from ring.tests.factories.notifications.notification_factory import (
    NotificationFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestNotificationCrud:
    """Test suite for notification CRUD helpers."""

    def test_create_notification(self, db_session: Session) -> None:
        user = UserFactory.create()
        notification = create_notification(
            db_session,
            recipient=user,
            type=NotificationType.LETTER_SENT,
            title="A new letter",
            body="Ring Newsletter #1 is here",
            target_api_id="lttr_00000000-0000-0000-0000-000000000000",
        )
        db_session.commit()

        assert notification.api_identifier.startswith("notif_")
        assert notification.recipient == user
        assert notification.type == NotificationType.LETTER_SENT
        assert notification.title == "A new letter"
        assert notification.body == "Ring Newsletter #1 is here"
        assert (
            notification.target_api_id
            == "lttr_00000000-0000-0000-0000-000000000000"
        )
        assert notification.read_at is None
        assert notification.created_at is not None

    def test_list_notifications_scoped_to_user(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        other = UserFactory.create()
        mine = NotificationFactory.create(recipient=user)
        NotificationFactory.create(recipient=other)
        db_session.commit()

        notifications = list_notifications(db_session, user)
        assert [n.id for n in notifications] == [mine.id]

    def test_list_notifications_newest_first_and_paginated(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        created = [
            NotificationFactory.create(recipient=user) for _ in range(5)
        ]
        db_session.commit()

        listed = list_notifications(db_session, user, limit=3)
        assert [n.id for n in listed] == [n.id for n in reversed(created)][:3]

        second_page = list_notifications(db_session, user, limit=3, offset=3)
        assert [n.id for n in second_page] == [
            n.id for n in reversed(created)
        ][3:]

    def test_unread_filter_and_counts(self, db_session: Session) -> None:
        user = UserFactory.create()
        unread = NotificationFactory.create(recipient=user)
        read = NotificationFactory.create(recipient=user)
        mark_notification_read(db_session, read)
        db_session.commit()

        unread_only = list_notifications(db_session, user, unread_only=True)
        assert [n.id for n in unread_only] == [unread.id]
        assert count_notifications(db_session, user) == 2
        assert count_notifications(db_session, user, unread_only=True) == 1

    def test_mark_notification_read_and_unread(
        self, db_session: Session
    ) -> None:
        notification = NotificationFactory.create()
        db_session.commit()
        assert notification.read_at is None

        mark_notification_read(db_session, notification)
        db_session.commit()
        first_read_at = notification.read_at
        assert first_read_at is not None

        # Marking read twice keeps the original timestamp.
        mark_notification_read(db_session, notification)
        assert notification.read_at == first_read_at

        mark_notification_read(db_session, notification, read=False)
        db_session.commit()
        assert notification.read_at is None

    def test_mark_all_notifications_read(self, db_session: Session) -> None:
        user = UserFactory.create()
        other = UserFactory.create()
        for _ in range(3):
            NotificationFactory.create(recipient=user)
        other_notification = NotificationFactory.create(recipient=other)
        db_session.commit()

        updated = mark_all_notifications_read(db_session, user)
        db_session.commit()

        assert updated == 3
        assert count_notifications(db_session, user, unread_only=True) == 0
        db_session.refresh(other_notification)
        assert other_notification.read_at is None

    def test_delete_notification(self, db_session: Session) -> None:
        user = UserFactory.create()
        notification = NotificationFactory.create(recipient=user)
        db_session.commit()

        delete_notification(db_session, notification)
        db_session.commit()

        assert count_notifications(db_session, user) == 0
