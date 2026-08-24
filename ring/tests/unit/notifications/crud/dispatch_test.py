"""Tests for notification dispatch.

This module tests the fan-out helper that creates in-app notifications and
best-effort delivers web push for a product event.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from ring.notifications.constants import NotificationType
from ring.notifications.crud import dispatch
from ring.notifications.crud.notification import list_notifications
from ring.notifications.crud.subscription import create_subscription
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.tests.factories.parties.user_factory import UserFactory


class TestTargetUrl:
    """Test suite for notification target URL resolution."""

    def test_letter_target(self) -> None:
        url = dispatch.target_url("lttr_abc")
        assert url.endswith("/loops/lttr_abc")

    def test_group_target(self) -> None:
        url = dispatch.target_url("grp_abc")
        assert url.endswith("/groups/grp_abc")

    def test_unknown_prefix_falls_back_to_root(self) -> None:
        root = dispatch.target_url(None)
        assert dispatch.target_url("qstn_abc") == root


class TestNotifyUsers:
    """Test suite for the notify_users dispatch helper."""

    def test_creates_notification_per_recipient(
        self, db_session: Session
    ) -> None:
        users = [UserFactory.create() for _ in range(3)]
        db_session.commit()

        created = dispatch.notify_users(
            db_session,
            users,
            type=NotificationType.RESPONSES_OPEN,
            title="Letter open",
            body="Letter #1 is open for responses",
            target_api_id="lttr_abc",
        )
        db_session.commit()

        assert len(created) == 3
        for user in users:
            notifications = list_notifications(db_session, user)
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.RESPONSES_OPEN
            assert notifications[0].target_api_id == "lttr_abc"

    def test_pushes_to_every_subscription(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = UserFactory.create()
        db_session.commit()
        for i in range(2):
            create_subscription(
                db_session,
                SubscriptionCreate(
                    endpoint=f"https://push.example.com/{user.id}/{i}",
                    keys={"p256dh": "key", "auth": "auth"},
                    user_api_identifier=user.api_identifier,
                ),
            )
        db_session.commit()

        pushed: list[tuple[str, dict[str, str]]] = []
        monkeypatch.setattr(
            dispatch,
            "send_push_notification",
            lambda subscription, payload: pushed.append(
                (subscription.endpoint, payload)
            ),
        )

        dispatch.notify_users(
            db_session,
            [user],
            type=NotificationType.LETTER_SENT,
            title="A new letter",
            body="Read it now",
            target_api_id="lttr_abc",
        )

        assert len(pushed) == 2
        endpoints = {endpoint for endpoint, _ in pushed}
        assert endpoints == {
            f"https://push.example.com/{user.id}/0",
            f"https://push.example.com/{user.id}/1",
        }
        for _, payload in pushed:
            assert payload["title"] == "A new letter"
            assert payload["body"] == "Read it now"
            assert payload["url"].endswith("/loops/lttr_abc")

    def test_push_failure_does_not_break_dispatch(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = UserFactory.create()
        db_session.commit()
        create_subscription(
            db_session,
            SubscriptionCreate(
                endpoint=f"https://push.example.com/{user.id}",
                keys={"p256dh": "key", "auth": "auth"},
                user_api_identifier=user.api_identifier,
            ),
        )
        db_session.commit()

        def boom(subscription: object, payload: object) -> None:
            raise RuntimeError("push service down")

        monkeypatch.setattr(dispatch, "send_push_notification", boom)

        created = dispatch.notify_users(
            db_session,
            [user],
            type=NotificationType.GENERIC,
            title="Still lands",
        )
        db_session.commit()

        assert len(created) == 1
        assert len(list_notifications(db_session, user)) == 1
