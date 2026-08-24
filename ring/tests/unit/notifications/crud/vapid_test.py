"""Tests for web push sending and gone-subscription detection."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pywebpush import WebPushException
from sqlalchemy.orm import Session

from ring.notifications.crud import vapid
from ring.notifications.crud.subscription import create_subscription
from ring.notifications.schemas.subscription import SubscriptionCreate
from ring.tests.factories.parties.user_factory import UserFactory


def _make_subscription(db_session: Session):
    user = UserFactory.create()
    db_session.commit()
    subscription = create_subscription(
        db_session,
        SubscriptionCreate(
            endpoint="https://push.example.com/vapid",
            keys={"p256dh": "key", "auth": "auth"},
            user_api_identifier=user.api_identifier,
        ),
    )
    db_session.commit()
    return subscription


class TestSendPushNotification:
    """Test suite for gone-subscription detection in push sending."""

    def test_success_is_not_gone(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        subscription = _make_subscription(db_session)
        monkeypatch.setattr(vapid, "webpush", lambda **kwargs: "ok")

        assert (
            vapid.send_push_notification(subscription, {"title": "t"}) is False
        )

    @pytest.mark.parametrize("status_code", [404, 410])
    def test_gone_status_codes_report_gone(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
        status_code: int,
    ) -> None:
        subscription = _make_subscription(db_session)

        def raise_gone(**kwargs: object) -> None:
            raise WebPushException(
                "gone",
                response=SimpleNamespace(status_code=status_code),
            )

        monkeypatch.setattr(vapid, "webpush", raise_gone)

        assert (
            vapid.send_push_notification(subscription, {"title": "t"}) is True
        )

    def test_transient_error_is_not_gone(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        subscription = _make_subscription(db_session)

        def raise_server_error(**kwargs: object) -> None:
            raise WebPushException(
                "boom",
                response=SimpleNamespace(status_code=500),
            )

        monkeypatch.setattr(vapid, "webpush", raise_server_error)

        assert (
            vapid.send_push_notification(subscription, {"title": "t"}) is False
        )
