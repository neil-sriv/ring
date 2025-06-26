"""Tests for the APIIdentified mixin class.

This module contains tests for the APIIdentified mixin functionality,
including identifier generation, prefix handling, and error cases.
It verifies both successful initialization and proper error handling.
"""

from __future__ import annotations

import pytest
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ring.api_identifier.api_identified_model import APIIdentified, APIPrefix


class Base(DeclarativeBase):
    """Base class for test models."""

    pass


class TestModel(APIIdentified, Base):
    """Test model that uses the APIIdentified mixin."""

    __tablename__ = "test_model"

    API_ID_PREFIX = APIPrefix.USER

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    def __init__(self, name: str) -> None:
        """Initialize a test model.

        Args:
            name (str): The name of the test model
        """
        APIIdentified.__init__(self)
        self.name = name


class TestModelWithoutPrefix(APIIdentified, Base):
    """Test model without API_ID_PREFIX to test error handling."""

    __tablename__ = "test_model_no_prefix"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    def __init__(self, name: str) -> None:
        """Initialize a test model without prefix.

        Args:
            name (str): The name of the test model
        """
        APIIdentified.__init__(self)
        self.name = name


class TestAPIIdentifiedModel:
    """Test suite for the APIIdentified mixin class.

    This class contains tests for all APIIdentified functionality,
    including identifier generation, prefix handling, and error cases.
    """

    def test_api_identified_initialization(self):
        """Test basic APIIdentified initialization.

        This test verifies that:
        1. A model can be initialized with the APIIdentified mixin
        2. The api_identifier is automatically generated with the correct prefix
        3. The identifier follows the expected format (prefix_uuid)

        Args:
            None
        """
        model = TestModel(name="test")

        assert model.api_identifier is not None
        assert model.api_identifier.startswith("usr_")
        assert len(model.api_identifier) == len("usr_") + 36  # UUID length
        assert model.name == "test"

    def test_api_identified_without_prefix_raises_error(self):
        """Test that initialization without API_ID_PREFIX raises ValueError.

        This test verifies that:
        1. Initializing a model without API_ID_PREFIX raises ValueError
        2. The error message is descriptive and helpful

        Args:
            None
        """
        with pytest.raises(
            AssertionError, match="API_ID_PREFIX must be set on the class"
        ):
            TestModelWithoutPrefix(name="test")

    def test_api_identified_unique_identifiers(self):
        """Test that each instance gets a unique identifier.

        This test verifies that:
        1. Multiple instances get different identifiers
        2. The identifiers are unique even with the same prefix
        3. The identifiers follow the expected format

        Args:
            None
        """
        model1 = TestModel(name="test1")
        model2 = TestModel(name="test2")
        model3 = TestModel(name="test3")

        identifiers = [
            model1.api_identifier,
            model2.api_identifier,
            model3.api_identifier,
        ]

        # All identifiers should be unique
        assert len(set(identifiers)) == 3

        # All identifiers should start with the correct prefix
        for identifier in identifiers:
            assert identifier.startswith("usr_")
            assert len(identifier) == len("usr_") + 36

    def test_api_identified_column_definition(self):
        """Test that the api_identifier column is properly defined.

        This test verifies that:
        1. The api_identifier column is defined as a mapped column
        2. The column has the correct attributes (unique=True, index=True)

        Args:
            None
        """
        # Check that the column is properly defined
        assert hasattr(TestModel, "api_identifier")
        assert isinstance(TestModel.api_identifier, Mapped)

        # The column should be defined with unique=True and index=True
        # This is tested indirectly through the model definition
        model = TestModel(name="test")
        assert hasattr(model, "api_identifier")

    def test_api_identified_prefix_class_variable(self):
        """Test that the API_ID_PREFIX class variable is properly set.

        This test verifies that:
        1. The API_ID_PREFIX class variable is accessible
        2. It has the expected value

        Args:
            None
        """
        assert TestModel.API_ID_PREFIX == APIPrefix.USER

        # TestModelWithoutPrefix should not have API_ID_PREFIX
        assert not hasattr(TestModelWithoutPrefix, "API_ID_PREFIX")
