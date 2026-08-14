"""Tests for authentication API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.one_time_token_model import OneTimeToken, TokenType
from ring.security import verify_password
from ring.tests.factories.parties.one_time_token_factory import (
    OneTimeTokenFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestAuthnAPI:
    """Test suite for login / authn API endpoints."""

    _RESET_REQUEST_MESSAGE = (
        "If an account exists for that email, "
        "a password recovery email has been sent"
    )

    def test_deprecated_endpoints_return_501(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Deprecated auth endpoints should return 501, not an unhandled 500."""
        cases = [
            ("post", "/login/test-token"),
            ("post", "/password-recovery-html-content/test@example.com"),
        ]
        for method, path in cases:
            response = getattr(unauthenticated_client, method)(path)
            assert response.status_code == 501, path
            assert (
                response.json()["detail"]
                == "This endpoint is deprecated and not implemented"
            )

    def test_reset_password_request_unknown_email_does_not_enumerate(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        """Unknown emails get the same success body as known ones (no 400)."""
        unknown = "nobody-at-all@example.com"
        response = unauthenticated_client.post(
            f"/reset-password:request/{unknown}"
        )

        assert response.status_code == 200
        assert response.json()["message"] == self._RESET_REQUEST_MESSAGE
        assert (
            db_session.query(OneTimeToken)
            .filter(OneTimeToken.email == unknown)
            .count()
            == 0
        )

    def test_reset_password_request_known_email_queues_token(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        """Registered emails still mint a password-reset token."""
        user = UserFactory.create()
        db_session.commit()

        response = unauthenticated_client.post(
            f"/reset-password:request/{user.email}"
        )

        assert response.status_code == 200
        assert response.json()["message"] == self._RESET_REQUEST_MESSAGE
        tokens = (
            db_session.query(OneTimeToken)
            .filter(
                OneTimeToken.email == user.email,
                OneTimeToken.type == TokenType.PASSWORD_RESET,
            )
            .all()
        )
        assert len(tokens) == 1
        assert not tokens[0].used

    def test_reset_password_accepts_password_reset_token(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        """A token minted for a password reset sets the new password."""
        user = UserFactory.create(password="original-password")
        ott = OneTimeTokenFactory.create(
            type=TokenType.PASSWORD_RESET, email=user.email
        )
        db_session.commit()

        response = unauthenticated_client.post(
            f"/reset-password/{ott.token}",
            json={"new_password": "brand-new-password"},
        )

        assert response.status_code == 200
        db_session.refresh(user)
        db_session.refresh(ott)
        assert ott.used
        assert verify_password("brand-new-password", user.hashed_password)

    def test_reset_password_rejects_invite_token(
        self, unauthenticated_client: TestClient, db_session: Session
    ) -> None:
        """An invite token must not double as a password reset token.

        Invites are emailed before the account exists and are not consumed
        unless that specific link is used to register, so accepting one here
        would let anyone holding an outstanding invite link take the account
        over once it is created.
        """
        user = UserFactory.create(password="original-password")
        ott = OneTimeTokenFactory.create(
            type=TokenType.INVITE, email=user.email
        )
        db_session.commit()

        response = unauthenticated_client.post(
            f"/reset-password/{ott.token}",
            json={"new_password": "attacker-password"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid token"
        db_session.refresh(user)
        db_session.refresh(ott)
        assert not ott.used
        assert verify_password("original-password", user.hashed_password)
