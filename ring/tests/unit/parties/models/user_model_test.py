"""Tests for the user model.

This module contains tests for the user model's functionality,
including model creation, relationships, and authentication.
It verifies both model attributes and relationships with other models.
"""
from __future__ import annotations

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.parties.crud.user import get_password_hash
from ring.parties.models.user_model import User
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestUserModel:
    """Test suite for the user model.

    This class contains tests for all user model functionality,
    including model creation, relationships, and authentication.
    """

    def test_user_model(self, faker: Faker, db_session: Session) -> None:
        """Test basic user model creation and attributes.

        This test verifies that:
        1. A user can be created with email, name, and password
        2. The user has the correct email, name, and hashed password
        3. The user has the correct API identifier prefix
        4. The user has valid ID and creation timestamp
        5. The user is properly stored in the database

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User.create(
            email=email, name="test", hashed_password=hashed_password
        )
        db_session.add(user)
        db_session.commit()

        assert user.email == email
        assert user.name == "test"
        assert user.hashed_password == hashed_password
        assert user.api_identifier.startswith(User.API_ID_PREFIX)
        assert user.id is not None
        assert user.created_at is not None

        db_user = db_session.scalars(
            sqlalchemy.select(User).filter(User.email == email)
        ).one()
        assert db_user == user

    def test_user_model_with_group(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test user model's relationship with groups.

        This test verifies that:
        1. A new user has no groups
        2. A user can be added to a group
        3. The user can access their groups
        4. The relationship is properly stored

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User(email=email, name="test", hashed_password=hashed_password)
        db_session.add(user)
        db_session.commit()

        assert user.groups == []

        group = GroupFactory.create()
        user.groups = [group]
        db_session.commit()

        assert user.groups == [group]

    def test_user_model_with_response(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test user model's relationship with responses.

        This test verifies that:
        1. A new user has no responses
        2. A response can be associated with the user
        3. The user can access their responses
        4. The relationship is properly stored

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User(email=email, name="test", hashed_password=hashed_password)
        db_session.add(user)
        db_session.commit()

        assert user.responses == []

        response = ResponseFactory.create(participant=user)
        db_session.commit()

        assert user.responses == [response]
