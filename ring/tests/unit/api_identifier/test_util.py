"""Tests for the API identifier utility functions.

This module contains tests for all API identifier utility functionality,
including exception handling, class registration, and database operations.
It verifies both successful operations and proper error handling.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from ring.api_identifier.util import (
    APIClassRegistration,
    APIIdentifierException,
    APIPrefix,
    IDNotFoundException,
    bulk_get_models,
    get_class_from_prefix,
    get_model,
    get_models,
)
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestAPIPrefix:
    """Test suite for the APIPrefix enum.

    This class contains tests for the APIPrefix enum functionality.
    """

    def test_api_prefix_values(self):
        """Test that APIPrefix enum has the expected values.

        This test verifies that:
        1. All expected prefixes are defined
        2. The values are correct strings

        Args:
            None
        """
        assert APIPrefix.USER.value == "usr"
        assert APIPrefix.GROUP.value == "grp"
        assert APIPrefix.INVITE.value == "inv"
        assert APIPrefix.LETTER.value == "lttr"
        assert APIPrefix.QUESTION.value == "qstn"
        assert APIPrefix.RESPONSE.value == "rspn"
        assert APIPrefix.DEFAULT_QUESTION.value == "dfqstn"
        assert APIPrefix.SUBSCRIPTION.value == "sbscrp"

    def test_api_prefix_from_string(self):
        """Test creating APIPrefix from string value.

        This test verifies that:
        1. APIPrefix can be created from string values
        2. Invalid strings raise ValueError

        Args:
            None
        """
        assert APIPrefix("usr") == APIPrefix.USER
        assert APIPrefix("grp") == APIPrefix.GROUP

        with pytest.raises(ValueError):
            APIPrefix("invalid")


class TestAPIClassRegistration:
    """Test suite for the APIClassRegistration dataclass.

    This class contains tests for the APIClassRegistration dataclass.
    """

    def test_api_class_registration_creation(self):
        """Test creating APIClassRegistration instances.

        This test verifies that:
        1. APIClassRegistration can be created with model_class and prefix
        2. The attributes are properly set

        Args:
            None
        """
        registration = APIClassRegistration(model_class=User, prefix="usr")

        assert registration.model_class == User
        assert registration.prefix == "usr"


class TestAPIIdentifierException:
    """Test suite for the APIIdentifierException class.

    This class contains tests for the APIIdentifierException functionality.
    """

    def test_api_identifier_exception_creation(self):
        """Test creating APIIdentifierException instances.

        This test verifies that:
        1. APIIdentifierException can be created with model_class and message
        2. The exception inherits from HTTPException
        3. The attributes are properly set

        Args:
            None
        """
        exception = APIIdentifierException(
            model_cls=User, message="Test error message"
        )

        assert exception.model_cls == User
        assert exception.status_code == 404
        assert exception.detail == "Test error message"

    def test_api_identifier_exception_without_message(self):
        """Test creating APIIdentifierException without custom message.

        This test verifies that:
        1. APIIdentifierException can be created without a custom message
        2. The detail is set to the default HTTPException message

        Args:
            None
        """
        exception = APIIdentifierException(model_cls=User)

        assert exception.model_cls == User
        assert exception.status_code == 404
        assert exception.detail == "Not Found"


class TestIDNotFoundException:
    """Test suite for the IDNotFoundException class.

    This class contains tests for the IDNotFoundException functionality.
    """

    def test_id_not_found_exception_creation(self):
        """Test creating IDNotFoundException instances.

        This test verifies that:
        1. IDNotFoundException can be created with model_class and api_ids
        2. The exception inherits from APIIdentifierException
        3. The api_ids attribute is properly set
        4. The detail message is formatted correctly

        Args:
            None
        """
        api_ids = ["usr_123", "usr_456"]
        exception = IDNotFoundException(User, api_ids)

        assert exception.model_cls == User
        assert exception.api_ids == api_ids
        assert exception.status_code == 404
        assert "usr_123,usr_456" in exception.detail
        assert User.__name__ in exception.detail

    def test_id_not_found_exception_single_id(self):
        """Test creating IDNotFoundException with a single ID.

        This test verifies that:
        1. IDNotFoundException works correctly with a single ID
        2. The detail message is formatted correctly

        Args:
            None
        """
        api_ids = ["usr_123"]
        exception = IDNotFoundException(User, api_ids)

        assert exception.api_ids == api_ids
        assert "usr_123" in exception.detail


class TestGetClassFromPrefix:
    """Test suite for the get_class_from_prefix function.

    This class contains tests for the get_class_from_prefix functionality.
    """

    def test_get_class_from_prefix_success(self):
        """Test getting class from prefix successfully.

        This test verifies that:
        1. get_class_from_prefix returns the correct model class
        2. It works with registered prefixes

        Args:
            None
        """
        user_class = get_class_from_prefix("usr")
        group_class = get_class_from_prefix("grp")

        assert user_class == User
        assert group_class == Group

    def test_get_class_from_prefix_invalid(self):
        """Test getting class from invalid prefix.

        This test verifies that:
        1. get_class_from_prefix raises ValueError for unregistered prefixes
        2. The error is properly handled

        Args:
            None
        """
        with pytest.raises(ValueError):
            get_class_from_prefix("invalid")


class TestGetModel:
    """Test suite for the get_model function.

    This class contains tests for the get_model functionality.
    """

    def test_get_model_success(self, db_session: Session):
        """Test getting a single model successfully.

        This test verifies that:
        1. get_model returns the correct model instance
        2. It works with valid API identifiers

        Args:
            db_session (Session): Database session
        """
        # Create a test user using the factory
        user = UserFactory.create()
        db_session.commit()

        # Retrieve the user by API identifier
        retrieved_user = get_model(db_session, User, user.api_identifier)

        assert retrieved_user == user
        assert retrieved_user.email == user.email

    def test_get_model_not_found(self, db_session: Session):
        """Test getting a model that doesn't exist.

        This test verifies that:
        1. get_model raises IDNotFoundException for non-existent IDs
        2. The exception contains the correct information

        Args:
            db_session (Session): Database session
        """
        with pytest.raises(IDNotFoundException) as exc_info:
            get_model(db_session, User, "usr_nonexistent")

        assert exc_info.value.model_cls == User
        assert exc_info.value.api_ids == ["usr_nonexistent"]


class TestGetModels:
    """Test suite for the get_models function.

    This class contains tests for the get_models functionality.
    """

    def test_get_models_success(self, db_session: Session):
        """Test getting multiple models successfully.

        This test verifies that:
        1. get_models returns the correct model instances
        2. It works with valid API identifiers
        3. All requested models are returned

        Args:
            db_session (Session): Database session
        """
        # Create test users using the factory
        users = [UserFactory.create() for _ in range(3)]
        db_session.commit()

        api_ids = [user.api_identifier for user in users]

        # Retrieve users by API identifiers
        retrieved_users = get_models(db_session, User, api_ids)

        assert len(retrieved_users) == 3
        assert all(user in retrieved_users for user in users)

    def test_get_models_partial_not_found(self, db_session: Session):
        """Test getting models when some don't exist.

        This test verifies that:
        1. get_models raises IDNotFoundException when some IDs don't exist
        2. The exception contains the correct missing IDs

        Args:
            db_session (Session): Database session
        """
        # Create one test user
        user = UserFactory.create()
        db_session.commit()

        api_ids = [user.api_identifier, "usr_nonexistent1", "usr_nonexistent2"]
        missing_ids = ["usr_nonexistent1", "usr_nonexistent2"]

        with pytest.raises(IDNotFoundException) as exc_info:
            get_models(db_session, User, api_ids)

        assert exc_info.value.model_cls == User
        # Check that all expected missing IDs are present, regardless of order
        assert set(exc_info.value.api_ids) == set(missing_ids)
        assert user.api_identifier not in exc_info.value.api_ids

    def test_get_models_all_not_found(self, db_session: Session):
        """Test getting models when none exist.

        This test verifies that:
        1. get_models raises IDNotFoundException when no IDs exist
        2. The exception contains all the missing IDs

        Args:
            db_session (Session): Database session
        """
        api_ids = ["usr_nonexistent1", "usr_nonexistent2"]

        with pytest.raises(IDNotFoundException) as exc_info:
            get_models(db_session, User, api_ids)

        assert exc_info.value.model_cls == User
        # Check that all expected IDs are present, regardless of order
        assert set(exc_info.value.api_ids) == set(api_ids)


class TestBulkGetModels:
    """Test suite for the bulk_get_models function.

    This class contains tests for the bulk_get_models functionality.
    """

    def test_bulk_get_models_success(self, db_session: Session):
        """Test getting multiple models of different types successfully.

        This test verifies that:
        1. bulk_get_models returns the correct model instances
        2. It works with different model types
        3. All requested models are returned

        Args:
            db_session (Session): Database session
        """
        # Create test models of different types using factories
        user = UserFactory.create()
        group = GroupFactory.create()
        letter = LetterFactory.create()

        db_session.commit()

        api_ids = [
            user.api_identifier,
            group.api_identifier,
            letter.api_identifier,
        ]

        # Retrieve models by API identifiers
        retrieved_models = bulk_get_models(db_session, api_ids)

        assert len(retrieved_models) == 3
        assert user in retrieved_models
        assert group in retrieved_models
        assert letter in retrieved_models

    def test_bulk_get_models_same_type(self, db_session: Session):
        """Test getting multiple models of the same type.

        This test verifies that:
        1. bulk_get_models works correctly with multiple models of the same type
        2. All models are returned correctly

        Args:
            db_session (Session): Database session
        """
        # Create multiple test users using the factory
        users = [UserFactory.create() for _ in range(3)]
        db_session.commit()

        api_ids = [user.api_identifier for user in users]

        # Retrieve users by API identifiers
        retrieved_models = bulk_get_models(db_session, api_ids)

        assert len(retrieved_models) == 3
        assert all(user in retrieved_models for user in users)

    def test_bulk_get_models_empty_list(self, db_session: Session):
        """Test getting models with empty list.

        This test verifies that:
        1. bulk_get_models returns empty list when no IDs provided
        2. No errors are raised

        Args:
            db_session (Session): Database session
        """
        retrieved_models = bulk_get_models(db_session, [])

        assert retrieved_models == []

    def test_bulk_get_models_invalid_prefix(self, db_session: Session):
        """Test getting models with invalid prefix.

        This test verifies that:
        1. bulk_get_models raises ValueError for invalid prefixes
        2. The error is properly handled

        Args:
            db_session (Session): Database session
        """
        api_ids = ["invalid_123"]

        with pytest.raises(ValueError):
            bulk_get_models(db_session, api_ids)
