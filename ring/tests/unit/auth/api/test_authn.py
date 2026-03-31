"""Tests for the authentication API endpoints.

This module contains tests for authentication endpoints, including login,
token refresh, and impersonation. It verifies both successful operations
and error cases for refresh token functionality.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from ring.fastapp.config import get_config
from ring.security import (
    ACCESS_TOKEN_TTL,
    REFRESH_TOKEN_TTL,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestLoginAccessToken:
    """Test suite for the login access token endpoint."""

    def test_login_returns_access_and_refresh_tokens(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test that login returns both access and refresh tokens.

        This test verifies that:
        1. Login with valid credentials returns 200
        2. Response includes access_token
        3. Response includes refresh_token
        4. token_type is 'bearer'
        """
        password = faker.password()
        user = UserFactory.create(password=password)
        db_session.commit()

        response = unauthenticated_client.post(
            "/login/access-token",
            data={
                "username": user.email,
                "password": password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify access token can be decoded and has correct type
        config = get_config()
        access_payload = jwt.decode(
            data["access_token"],
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )
        assert access_payload["sub"] == user.email
        assert access_payload["type"] == TokenType.ACCESS.value

        # Verify refresh token can be decoded and has correct type
        refresh_payload = jwt.decode(
            data["refresh_token"],
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )
        assert refresh_payload["sub"] == user.email
        assert refresh_payload["type"] == TokenType.REFRESH.value

    def test_login_with_invalid_credentials_fails(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test that login with invalid credentials fails.

        This test verifies that:
        1. Login with wrong password returns 400
        2. Login with non-existent user returns 400
        3. Response contains appropriate error message
        """
        password = faker.password()
        user = UserFactory.create(password=password)
        db_session.commit()

        # Test with wrong password
        response = unauthenticated_client.post(
            "/login/access-token",
            data={
                "username": user.email,
                "password": "wrong_password",
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect username or password"

        # Test with non-existent user
        response = unauthenticated_client.post(
            "/login/access-token",
            data={
                "username": "nonexistent@example.com",
                "password": password,
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect username or password"


class TestRefreshToken:
    """Test suite for the refresh token endpoint."""

    def test_refresh_token_returns_new_tokens(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that a valid refresh token returns new access and refresh tokens.

        This test verifies that:
        1. Refresh endpoint returns 200 with valid refresh token
        2. Response includes new access_token
        3. Response includes new refresh_token
        4. New tokens have correct types
        """
        user = UserFactory.create()
        db_session.commit()

        refresh_token = create_refresh_token(data={"sub": user.email})

        response = unauthenticated_client.post(
            "/login/refresh-token",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify new tokens are different
        assert data["refresh_token"] != refresh_token

        # Verify new access token can be decoded
        config = get_config()
        access_payload = jwt.decode(
            data["access_token"],
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )
        assert access_payload["sub"] == user.email
        assert access_payload["type"] == TokenType.ACCESS.value

    def test_refresh_token_fails_with_access_token(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that using an access token as refresh token fails.

        This test verifies that:
        1. Refresh endpoint rejects access tokens
        2. Response returns 401 with appropriate error
        """
        user = UserFactory.create()
        db_session.commit()

        access_token = create_access_token(data={"sub": user.email})

        response = unauthenticated_client.post(
            "/login/refresh-token",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token type"

    def test_refresh_token_fails_with_expired_token(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that an expired refresh token fails.

        This test verifies that:
        1. Refresh endpoint rejects expired tokens
        2. Response returns 401
        """
        user = UserFactory.create()
        db_session.commit()

        # Create an expired refresh token
        expired_refresh_token = create_refresh_token(
            data={"sub": user.email}, expires_ttl=-1
        )

        response = unauthenticated_client.post(
            "/login/refresh-token",
            json={"refresh_token": expired_refresh_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_refresh_token_fails_with_invalid_token(
        self,
        unauthenticated_client: TestClient,
    ) -> None:
        """Test that an invalid refresh token fails.

        This test verifies that:
        1. Refresh endpoint rejects malformed tokens
        2. Response returns 401
        """
        response = unauthenticated_client.post(
            "/login/refresh-token",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_refresh_token_fails_with_deleted_user(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that refresh token fails if user no longer exists.

        This test verifies that:
        1. Refresh endpoint checks user existence
        2. Response returns 401 if user was deleted
        """
        user = UserFactory.create()
        db_session.commit()

        refresh_token = create_refresh_token(data={"sub": user.email})

        # Delete the user
        db_session.delete(user)
        db_session.commit()

        response = unauthenticated_client.post(
            "/login/refresh-token",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "User not found"


class TestTokenCreation:
    """Test suite for token creation functions."""

    def test_access_token_has_correct_expiry(self) -> None:
        """Test that access tokens have the correct expiration time.

        This test verifies that:
        1. Access token expiry is set correctly
        2. Default TTL is used when not specified
        """
        email = "test@example.com"
        token = create_access_token(data={"sub": email})

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(tz=UTC) + timedelta(
            seconds=ACCESS_TOKEN_TTL
        )

        # Allow 5 seconds tolerance
        assert abs((exp - expected_exp).total_seconds()) < 5

    def test_refresh_token_has_correct_expiry(self) -> None:
        """Test that refresh tokens have the correct expiration time.

        This test verifies that:
        1. Refresh token expiry is set correctly
        2. Default TTL is used when not specified
        """
        email = "test@example.com"
        token = create_refresh_token(data={"sub": email})

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(tz=UTC) + timedelta(
            seconds=REFRESH_TOKEN_TTL
        )

        # Allow 5 seconds tolerance
        assert abs((exp - expected_exp).total_seconds()) < 5

    def test_access_token_has_access_type(self) -> None:
        """Test that access tokens have the correct type claim."""
        email = "test@example.com"
        token = create_access_token(data={"sub": email})

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        assert payload["type"] == TokenType.ACCESS.value

    def test_refresh_token_has_refresh_type(self) -> None:
        """Test that refresh tokens have the correct type claim."""
        email = "test@example.com"
        token = create_refresh_token(data={"sub": email})

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        assert payload["type"] == TokenType.REFRESH.value

    def test_custom_ttl_for_access_token(self) -> None:
        """Test that custom TTL can be set for access tokens."""
        email = "test@example.com"
        custom_ttl = 3600  # 1 hour
        token = create_access_token(
            data={"sub": email}, expires_ttl=custom_ttl
        )

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(tz=UTC) + timedelta(seconds=custom_ttl)

        # Allow 5 seconds tolerance
        assert abs((exp - expected_exp).total_seconds()) < 5

    def test_custom_ttl_for_refresh_token(self) -> None:
        """Test that custom TTL can be set for refresh tokens."""
        email = "test@example.com"
        custom_ttl = 86400  # 1 day
        token = create_refresh_token(
            data={"sub": email}, expires_ttl=custom_ttl
        )

        config = get_config()
        payload = jwt.decode(
            token,
            config.JWT_SIGNING_KEY,
            algorithms=[config.JWT_SIGNING_ALGORITHM],
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(tz=UTC) + timedelta(seconds=custom_ttl)

        # Allow 5 seconds tolerance
        assert abs((exp - expected_exp).total_seconds()) < 5


class TestDecodeRefreshToken:
    """Test suite for the decode_refresh_token function."""

    def test_decode_refresh_token_success(self) -> None:
        """Test successful decoding of a valid refresh token."""
        email = "test@example.com"
        token = create_refresh_token(data={"sub": email})

        result = decode_refresh_token(token)

        assert result == email

    def test_decode_refresh_token_rejects_access_token(self) -> None:
        """Test that decode_refresh_token rejects access tokens."""
        email = "test@example.com"
        token = create_access_token(data={"sub": email})

        with pytest.raises(Exception) as exc_info:
            decode_refresh_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token type"

    def test_decode_refresh_token_rejects_expired_token(self) -> None:
        """Test that decode_refresh_token rejects expired tokens."""
        email = "test@example.com"
        token = create_refresh_token(data={"sub": email}, expires_ttl=-1)

        with pytest.raises(Exception) as exc_info:
            decode_refresh_token(token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    def test_decode_refresh_token_rejects_invalid_token(self) -> None:
        """Test that decode_refresh_token rejects invalid tokens."""
        with pytest.raises(Exception) as exc_info:
            decode_refresh_token("invalid_token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
