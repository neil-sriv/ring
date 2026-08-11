"""Tests for authentication API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.one_time_token_model import TokenType
from ring.security import verify_password
from ring.tests.factories.parties.one_time_token_factory import (
    OneTimeTokenFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestAuthnAPI:
    """Test suite for login / authn API endpoints."""

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
