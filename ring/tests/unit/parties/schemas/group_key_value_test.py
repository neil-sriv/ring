"""Tests for group key-value schemas."""

import pytest
from pydantic import ValidationError

from ring.parties.schemas.group_key_value import (
    BulkGroupKeyValueUpdate,
    SingleGroupKeyValueBase,
    SingleGroupKeyValueUpdate,
)


class TestSingleGroupKeyValueBase:
    """Tests for SingleGroupKeyValueBase schema."""

    def test_valid_data(self):
        """Test schema with valid data."""
        # Test simple types
        kv = SingleGroupKeyValueBase(key="test_key", value="test_value")
        assert kv.key == "test_key"
        assert kv.value == "test_value"

        # Test complex types
        complex_value = {
            "nested": {"value": 42},
            "list": [1, 2, {"nested": "value"}],
        }
        kv = SingleGroupKeyValueBase(key="complex_key", value=complex_value)
        assert kv.key == "complex_key"
        assert kv.value == complex_value

    def test_missing_fields(self):
        """Test schema validation with missing fields."""
        with pytest.raises(ValidationError) as exc_info:
            SingleGroupKeyValueBase(key="test_key")
        assert "value" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            SingleGroupKeyValueBase(value="test_value")
        assert "key" in str(exc_info.value)


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

    def test_set_operation_without_value(self):
        """Test set operation validation when value is missing."""
        with pytest.raises(ValidationError) as exc_info:
            SingleGroupKeyValueUpdate(key="test_key", operation="set")
        assert "value is required for 'set' operation" in str(exc_info.value)

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

    def test_invalid_update_in_bulk(self):
        """Test bulk schema with invalid update."""
        with pytest.raises(ValidationError) as exc_info:
            BulkGroupKeyValueUpdate(
                updates=[
                    SingleGroupKeyValueUpdate(
                        key="key1", value="value1", operation="set"
                    ),
                    # Invalid update - set operation without value
                    SingleGroupKeyValueUpdate(key="key2", operation="set"),
                ]
            )
        assert "value is required for 'set' operation" in str(exc_info.value)
