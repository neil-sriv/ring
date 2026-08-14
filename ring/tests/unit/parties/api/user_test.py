"""Tests for the user API endpoints.

This module contains tests for all user-related API endpoints, including
user creation, registration, authentication, and profile management.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

import pytest
import sqlalchemy
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.invite_factory import InviteFactory
from ring.tests.factories.parties.one_time_token_factory import (
    OneTimeTokenFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)
from ring.tests.unit.conftest import TClientForUser


class TestUserAPI:
    """Test suite for user API endpoints.

    This class contains tests for all user-related API operations,
    including authentication, registration, and profile management.
    """

    def test_read_me_authenticated(
        self, get_client_for_user: TClientForUser, db_session: Session
    ):
        """Test reading the current user's profile when authenticated.

        This test verifies that:
        1. The authenticated user can read their own profile
        2. The response contains the correct user data
        3. The email matches what was set

        Args:
            get_client_for_user (TClientForUser): Function to get a client for a specific user
            db_session (Session): Database session
        """
        user = UserFactory.create(email="test@gmail.com")
        db_session.commit()
        client = get_client_for_user(user)
        response = client.get("/parties/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@gmail.com"

    def test_read_me_unauthenticated(self, unauthenticated_client: TestClient):
        """Test reading the current user's profile when not authenticated.

        This test verifies that:
        1. Unauthenticated users cannot read their profile
        2. The response contains the correct error message

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
        """
        response = unauthenticated_client.get("/parties/me")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_create_user(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test creating a new user with valid data.

        This test verifies that:
        1. A user can be created with valid email, name, and password
        2. The response contains the correct user data
        3. The user is properly stored in the database

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        email, name, password = faker.email(), faker.name(), faker.password()
        input: dict[str, str] = {
            "email": email,
            "name": name,
            "password": password,
        }
        resp = unauthenticated_client.post("/parties/user", json=input)

        assert resp.status_code == 201
        data = resp.json()
        assert data == data | {
            "email": email,
            "name": name,
        }
        assert db_session.scalar(
            sqlalchemy.select(User).where(User.email == email)
        )

    def test_create_user_duplicate(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test creating a user with a duplicate email.

        This test verifies that:
        1. Creating a user with an existing email fails
        2. The response contains the correct error message
        3. The database state remains unchanged

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        db_user = UserFactory.create()
        db_session.commit()

        input: dict[str, str] = {
            "email": db_user.email,
            "name": db_user.name or "name",
            "password": faker.password(),
        }
        resp = unauthenticated_client.post("/parties/user", json=input)

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_register_user(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test registering a user with a valid invite token.

        This test verifies that:
        1. A user can register with a valid invite token
        2. The user is added to the invited group
        3. The token is marked as used
        4. The response contains the correct user data

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        invite = InviteFactory.create()
        db_session.commit()

        email, name, password = invite.email, faker.name(), faker.password()

        input = {
            "email": email,
            "name": name,
            "password": password,
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data == data | {
            "email": email,
            "name": name,
        }

        db_user = db_session.scalar(
            sqlalchemy.select(User).where(User.email == email)
        )
        assert db_user
        assert db_user.email == email
        assert db_user.name == name

        assert db_user in invite.group.members

        assert invite.one_time_token.used

    def test_register_user_invalid_token(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test registering a user with invalid invite tokens.

        This test verifies that:
        1. Registration fails with an invalid token
        2. Registration fails with an expired token
        3. Registration fails with a used token
        4. The response contains the correct error message

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        input = {
            "email": faker.email(),
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            "/parties/register/invalid_token", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

        expired_token = OneTimeTokenFactory.create()
        expired_token.ttl = 0
        db_session.commit()

        resp = unauthenticated_client.post(
            f"/parties/register/{expired_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

        used_token = OneTimeTokenFactory.create()
        used_token.used = True
        db_session.commit()

        resp = unauthenticated_client.post(
            f"/parties/register/{used_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

    def test_register_user_email_mismatch(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test registering a user with an email mismatch.

        This test verifies that:
        1. Registration fails when the email doesn't match the invite
        2. The response contains the correct error message
        3. The database state remains unchanged

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        invite = InviteFactory.create(email="invite_email")
        db_session.commit()

        input = {
            "email": "different_email",
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email mismatch"

    def test_register_user_duplicate(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test registering a user with an email that already exists.

        This test verifies that:
        1. Registration fails when the email is already registered
        2. The response contains the correct error message
        3. The database state remains unchanged

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        invite = InviteFactory.create()
        db_session.commit()

        user = UserFactory.create(email=invite.email)
        db_session.commit()

        input = {
            "email": user.email,
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_register_email_case_insensitive(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test registering a user with case-insensitive email matching.

        This test verifies that:
        1. Email matching is case-insensitive
        2. The response contains the correct user data
        3. The email is stored in the correct case
        4. The user is added to the invited group

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        invite = InviteFactory.create(email="invite_email")
        db_session.commit()

        input = {
            "email": "INVITE_EMAIL",
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data == data | {
            "email": "invite_email",
            "name": input["name"],
        }

    def test_read_users(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test listing all users.

        This test verifies that:
        1. All users are returned in the response
        2. The response includes the current user
        3. The response includes users from the current user's group
        4. The response matches the database state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        users = [UserFactory.create() for _ in range(5)]
        group = GroupFactory.create(admin=current_user)
        group_users = [UserFactory.create() for _ in range(5)]
        for user in group_users:
            group.members.append(user)
        db_session.commit()

        resp = authenticated_client.get("/parties/users")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 11  # 10 users + current user
        assert_pydantic_models_json_dump_in_response_dict(
            users + group_users + [current_user], data
        )

    def test_read_user_by_id(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test reading a user by their API identifier.

        This test verifies that:
        1. A user can be retrieved by their API identifier
        2. The response contains the correct user data
        3. The response matches the database state
        4. All user fields are included in the response

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        user = UserFactory.create()
        db_session.commit()

        resp = authenticated_client.get(f"/parties/user/{user.api_identifier}")
        assert resp.status_code == 200
        data = resp.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(user, data)

    def test_read_user_by_id_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Test reading a non-existent user by API identifier.

        This test verifies that:
        1. Reading a non-existent user fails
        2. The response contains the correct error message
        3. The response indicates the user was not found
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        resp = authenticated_client.get("/parties/user/invalid_id")
        assert resp.status_code == 404
        data = resp.json()
        assert_api_model_not_found(data, User, ["invalid_id"])

    def test_update_user_me_name(
        self,
        authenticated_client: TestClient,
        current_user: User,
        faker: Faker,
    ) -> None:
        """Test updating the current user's name.

        This test verifies that:
        1. The user's name can be updated
        2. The response contains the updated user data
        3. The database is updated with the new name
        4. The change is reflected in the user object

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            faker (Faker): Faker instance for generating test data
        """
        new_name = faker.name()
        assert current_user.name != new_name
        input = {"name": new_name}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == new_name
        assert current_user.name == new_name

    def test_update_user_me_email(
        self,
        authenticated_client: TestClient,
        current_user: User,
        faker: Faker,
    ) -> None:
        """Test updating the current user's email.

        This test verifies that:
        1. The user's email can be updated
        2. The response contains the updated user data
        3. The database is updated with the new email
        4. The change is reflected in the user object

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            faker (Faker): Faker instance for generating test data
        """
        new_email = faker.email()
        assert current_user.email != new_email
        input = {"email": new_email}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == new_email
        assert current_user.email == new_email

    def test_update_user_me_email_duplicate(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test updating the current user's email to an existing email.

        This test verifies that:
        1. Updating to an existing email fails
        2. The response contains the correct error message
        3. The user's email remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        user = UserFactory.create()
        db_session.commit()

        input = {"email": user.email}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_update_user_me_password(
        self,
        authenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        """Test updating the current user's password.

        This test verifies that:
        1. The password can be updated with correct current password
        2. The response contains the success message
        3. The new password can be used for authentication
        4. The database state is updated correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            faker (Faker): Faker instance for generating test data
        """
        new_password = faker.password()
        input = {
            "current_password": "password",
            "new_password": new_password,
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Password updated successfully"

    def test_update_user_me_password_incorrect_password(
        self,
        authenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        """Test updating the current user's password with incorrect current password.

        This test verifies that:
        1. Updating with incorrect current password fails
        2. The response contains the correct error message
        3. The password remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            faker (Faker): Faker instance for generating test data
        """
        new_password = faker.password()
        input = {
            "current_password": "incorrect_password",
            "new_password": new_password,
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Incorrect password"

    def test_update_user_me_password_same_password(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Test updating the current user's password to the same password.

        This test verifies that:
        1. Updating to the same password fails
        2. The response contains the correct error message
        3. The password remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        input = {
            "current_password": "password",
            "new_password": "password",
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == "New password must be different from the current password"
        )

    @pytest.mark.admin(True)
    def test_update_user_admin(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test updating a user's admin status.

        This test verifies that:
        1. A user can be updated to admin status
        2. The response contains the updated user data
        3. The database is updated with the new admin status
        4. The change is reflected in the user object

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        user = UserFactory.create()
        db_session.commit()

        resp = authenticated_client.patch(
            f"/parties/{user.api_identifier}/admin"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "User admin status updated successfully"
        assert user.admin

        resp = authenticated_client.patch(
            f"/parties/{user.api_identifier}/admin"
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "User is already an admin"

        resp = authenticated_client.patch(f"/parties/invalid_id/admin")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Model ids not found"

    @pytest.mark.admin(True)
    def test_update_user_by_id(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Admins can update another user's name and email."""
        user = UserFactory.create()
        db_session.commit()

        new_name = faker.name()
        new_email = faker.email().lower()
        resp = authenticated_client.patch(
            f"/parties/user/{user.api_identifier}",
            json={"name": new_name, "email": new_email},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == new_name
        assert data["email"] == new_email
        assert user.name == new_name
        assert user.email == new_email

    @pytest.mark.admin(True)
    def test_update_user_by_id_duplicate_email(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Admin user update rejects emails already used by another account."""
        target = UserFactory.create()
        other = UserFactory.create()
        db_session.commit()

        resp = authenticated_client.patch(
            f"/parties/user/{target.api_identifier}",
            json={"email": other.email},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_update_user_by_id_requires_admin(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Non-admin callers cannot update another user."""
        user = UserFactory.create()
        db_session.commit()

        resp = authenticated_client.patch(
            f"/parties/user/{user.api_identifier}",
            json={"name": faker.name()},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Unauthorized"

    @pytest.mark.admin(True)
    def test_update_user_by_id_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Admin update returns not-found for unknown api ids."""
        resp = authenticated_client.patch(
            "/parties/user/invalid_id",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404
        assert_api_model_not_found(resp.json(), User, ["invalid_id"])

    def test_deprecated_endpoints_return_501(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Deprecated user endpoints should return 501, not an unhandled 500."""
        cases = [
            ("delete", "/parties/me"),
            ("post", "/parties/signup"),
            ("patch", "/parties/usr_example"),
            ("delete", "/parties/usr_example"),
        ]
        for method, path in cases:
            response = getattr(unauthenticated_client, method)(path)
            assert response.status_code == 501, path
            assert (
                response.json()["detail"]
                == "This endpoint is deprecated and not implemented"
            )
