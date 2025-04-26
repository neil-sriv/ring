"""Tests for the user CRUD operations.

This module contains tests for all user-related database operations,
including user creation, authentication, and retrieval.
It verifies both successful operations and error cases.
"""

from faker import Faker
from sqlalchemy.orm import Session

from ring.parties.crud import user as user_crud
from ring.tests.factories.parties.user_factory import UserFactory


class TestUserCrud:
    """Test suite for user CRUD operations.

    This class contains tests for all user-related database operations,
    including CRUD operations and authentication.
    """

    def test_get_users(self, db_session: Session) -> None:
        """Test retrieving all users.

        This test verifies that:
        1. An empty list is returned when no users exist
        2. All users are returned when they exist
        3. The returned list matches the created users

        Args:
            db_session (Session): Database session
        """
        assert user_crud.get_users(db_session) == []

        db_users = [UserFactory.create() for _ in range(10)]
        db_session.commit()

        users = user_crud.get_users(db_session)
        assert len(users) == 10
        assert users == db_users

    def test_authenticate_user(self, db_session: Session) -> None:
        """Test authenticating a user with valid credentials.

        This test verifies that:
        1. A user can be authenticated with correct email and password
        2. The correct user is returned
        3. The authentication is successful

        Args:
            db_session (Session): Database session
        """
        user = UserFactory.create(password="test password")
        db_session.commit()

        assert user == user_crud.authenticate_user(
            db_session, user.email, "test password"
        )

    def test_authenticate_user_invalid(self, db_session: Session) -> None:
        """Test authenticating a user with invalid credentials.

        This test verifies that:
        1. Authentication fails with incorrect password
        2. Authentication fails with non-existent email
        3. None is returned for invalid credentials

        Args:
            db_session (Session): Database session
        """
        user = UserFactory.create(password="test password")
        db_session.commit()

        assert (
            user_crud.authenticate_user(
                db_session, user.email, "invalid password"
            )
            is None
        )
        assert (
            user_crud.authenticate_user(
                db_session, "invalid email", "test password"
            )
            is None
        )

    def test_get_user_by_email(self, db_session: Session) -> None:
        """Test retrieving a user by email.

        This test verifies that:
        1. A user can be retrieved by their email
        2. The correct user is returned
        3. The email matches what was set

        Args:
            db_session (Session): Database session
        """
        user = UserFactory.create(email="test_email")
        db_session.commit()

        assert user_crud.get_user_by_email(db_session, "test_email") == user

    def test_get_user_by_email_invalid(self, db_session: Session) -> None:
        """Test retrieving a user with a non-existent email.

        This test verifies that:
        1. None is returned for non-existent email
        2. The database state remains unchanged

        Args:
            db_session (Session): Database session
        """
        UserFactory.create()
        db_session.commit()

        assert user_crud.get_user_by_email(db_session, "invalid_email") is None

    def test_create_user(self, db_session: Session, faker: Faker) -> None:
        """Test creating a new user.

        This test verifies that:
        1. A user can be created with valid data
        2. The user has the correct email, name, and password
        3. The user can be authenticated after creation
        4. The user is properly stored in the database

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        email, name, password = faker.email(), faker.name(), faker.password()
        user = user_crud.create_user(db_session, email, name, password)
        db_session.commit()

        assert user.email == email
        assert user.name == name
        assert user_crud.authenticate_user(db_session, user.email, password)

    def test_make_user_admin(self, db_session: Session) -> None:
        """Test making a user an admin.

        This test verifies that:
        1. A user can be made an admin
        2. The user's admin status is updated
        3. The database is updated with the new admin status
        4. The change is reflected in the user object

        Args:
            db_session (Session): Database session
        """
        user = UserFactory.create()
        db_session.commit()

        user_crud.make_user_admin(db_session, user)
        db_session.commit()

        assert user.admin
