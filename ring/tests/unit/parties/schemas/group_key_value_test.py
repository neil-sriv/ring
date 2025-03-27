"""Tests for group key-value schemas.

This module contains tests for all group key-value related Pydantic schemas,
including base schemas, update schemas, and bulk operation schemas.
It verifies both schema validation and data handling for various data types.
"""

import pytest
from pydantic import ValidationError

from ring.parties.schemas.group_key_value import (
    BulkGroupKeyValueUpdate,
    GroupKeyValue,
    GroupKeyValueBase,
    SingleGroupKeyValueUpdate,
)


class TestGroupKeyValueBase:
    """Test suite for GroupKeyValueBase schema.

    This class contains tests for the base key-value schema,
    including validation of simple and complex data types,
    and handling of required fields.
    """

    def test_valid_data(self):
        """Test schema with valid data.

        This test verifies that:
        1. Simple key-value pairs are accepted
        2. Complex nested data structures are accepted
        3. The schema correctly stores and retrieves values

        Returns:
            None
        """
        # Test simple types
        kv = GroupKeyValueBase(key="test_key", value="test_value")
        assert kv.key == "test_key"
        assert kv.value == "test_value"

        # Test complex types
        complex_value = {
            "nested": {"value": 42},
            "list": [1, 2, {"nested": "value"}],
        }
        kv = GroupKeyValueBase(key="complex_key", value=complex_value)
        assert kv.key == "complex_key"
        assert kv.value == complex_value

    def test_missing_fields(self):
        """Test schema validation with missing fields.

        This test verifies that:
        1. Missing key field raises validation error
        2. Missing value field raises validation error
        3. Error messages indicate the missing fields

        Returns:
            None
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupKeyValueBase(key="test_key")
        assert "value" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            GroupKeyValueBase(value="test_value")
        assert "key" in str(exc_info.value)


class TestGroupKeyvalue:
    """Test suite for GroupKeyValue schema.

    This class contains tests for the main group key-value schema,
    including validation of key-value collections and nested data structures.
    """

    def test_valid_data(self):
        """Test schema with valid data.

        This test verifies that:
        1. Simple key-value collections are accepted
        2. The schema correctly stores and retrieves values
        3. The data structure matches the input

        Returns:
            None
        """
        kv = GroupKeyValue(key_values={"test_key": "test_value"})
        assert kv.key_values == {"test_key": "test_value"}

    def test_nested_objects(self):
        """Test schema with nested objects.

        This test verifies that:
        1. Nested data structures are accepted
        2. The schema correctly stores and retrieves nested values
        3. The data structure maintains its hierarchy

        Returns:
            None
        """
        nested_value = {"nested": {"value": 42}}
        kv = GroupKeyValue(key_values={"test_key": nested_value})
        assert kv.key_values == {"test_key": nested_value}


class TestSingleGroupKeyValueUpdate:
    """Test suite for SingleGroupKeyValueUpdate schema.

    This class contains tests for single key-value update operations,
    including set and delete operations with various data types.
    """

    def test_set_operation(self):
        """Test schema with set operation.

        This test verifies that:
        1. Simple values can be set
        2. Complex nested values can be set
        3. The operation type is correctly stored
        4. The schema maintains data integrity

        Returns:
            None
        """
        # Test simple value
        update = SingleGroupKeyValueUpdate(
            key="test_key", value="test_value", operation="set"
        )
        assert update.key == "test_key"
        assert update.value == "test_value"
        assert update.operation == "set"

        # Test complex value
        complex_value = {"nested": {"value": 42}}
        update = SingleGroupKeyValueUpdate(
            key="complex_key", value=complex_value, operation="set"
        )
        assert update.value == complex_value

    def test_delete_operation(self):
        """Test schema with delete operation.

        This test verifies that:
        1. Delete operation is accepted
        2. Value is set to None for delete operations
        3. The operation type is correctly stored

        Returns:
            None
        """
        update = SingleGroupKeyValueUpdate(key="test_key", operation="delete")
        assert update.key == "test_key"
        assert update.operation == "delete"
        assert update.value is None

    def test_invalid_operation(self):
        """Test schema with invalid operation.

        This test verifies that:
        1. Invalid operations are rejected
        2. The error message indicates the invalid operation
        3. The schema maintains validation rules

        Returns:
            None
        """
        with pytest.raises(ValidationError) as exc_info:
            SingleGroupKeyValueUpdate(
                key="test_key", operation="invalid", value="test_value"
            )
        assert "operation" in str(exc_info.value)


class TestBulkGroupKeyValueUpdate:
    """Test suite for BulkGroupKeyValueUpdate schema.

    This class contains tests for bulk key-value update operations,
    including multiple updates in a single request and validation rules.
    """

    def test_valid_updates(self):
        """Test schema with valid updates.

        This test verifies that:
        1. Multiple updates can be included
        2. Different operation types can be mixed
        3. Complex data types are handled correctly
        4. The schema maintains data integrity

        Returns:
            None
        """
        updates = [
            SingleGroupKeyValueUpdate(
                key="key1", value="value1", operation="set"
            ),
            SingleGroupKeyValueUpdate(key="key2", operation="delete"),
            SingleGroupKeyValueUpdate(
                key="key3",
                value={"nested": "value"},
                operation="set",
            ),
        ]
        bulk_update = BulkGroupKeyValueUpdate(updates=updates)
        assert len(bulk_update.updates) == 3
        assert bulk_update.updates[0].key == "key1"
        assert bulk_update.updates[1].operation == "delete"
        assert bulk_update.updates[2].value == {"nested": "value"}

    def test_empty_updates(self):
        """Test schema with empty updates list.

        This test verifies that:
        1. Empty update lists are rejected
        2. The error message indicates the validation failure
        3. The schema enforces non-empty updates

        Returns:
            None
        """
        with pytest.raises(ValidationError) as exc_info:
            BulkGroupKeyValueUpdate(updates=[])
        assert "updates" in str(exc_info.value)
