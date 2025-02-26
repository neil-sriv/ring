"""Tests for group key-value schemas."""

import pytest
from pydantic import ValidationError

from ring.parties.schemas.group_key_value import (
    BulkGroupKeyValueUpdate,
    GroupKeyValue,
    GroupKeyValueBase,
    SingleGroupKeyValueUpdate,
)


class TestGroupKeyValueBase:
    """Tests for GroupKeyValueBase schema."""

    def test_valid_data(self):
        """Test schema with valid data."""
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
        """Test schema validation with missing fields."""
        with pytest.raises(ValidationError) as exc_info:
            GroupKeyValueBase(key="test_key")
        assert "value" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            GroupKeyValueBase(value="test_value")
        assert "key" in str(exc_info.value)


class TestGroupKeyvalue:
    """Tests for GroupKeyValue schema."""

    def test_valid_data(self):
        """Test schema with valid data."""
        kv = GroupKeyValue(key_values={"test_key": "test_value"})
        assert kv.key_values == {"test_key": "test_value"}

    def test_nested_objects(self):
        """Test schema with nested objects."""
        nested_value = {"nested": {"value": 42}}
        kv = GroupKeyValue(key_values={"test_key": nested_value})
        assert kv.key_values == {"test_key": nested_value}


class TestSingleGroupKeyValueUpdate:
    """Tests for SingleGroupKeyValueUpdate schema."""

    def test_set_operation(self):
        """Test schema with set operation."""
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
        """Test schema with delete operation."""
        update = SingleGroupKeyValueUpdate(key="test_key", operation="delete")
        assert update.key == "test_key"
        assert update.operation == "delete"
        assert update.value is None

    def test_invalid_operation(self):
        """Test schema with invalid operation."""
        with pytest.raises(ValidationError) as exc_info:
            SingleGroupKeyValueUpdate(
                key="test_key", operation="invalid", value="test_value"
            )
        assert "operation" in str(exc_info.value)


class TestBulkGroupKeyValueUpdate:
    """Tests for BulkGroupKeyValueUpdate schema."""

    def test_valid_updates(self):
        """Test schema with valid updates."""
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
        """Test schema with empty updates list."""
        with pytest.raises(ValidationError) as exc_info:
            BulkGroupKeyValueUpdate(updates=[])
        assert "updates" in str(exc_info.value)
