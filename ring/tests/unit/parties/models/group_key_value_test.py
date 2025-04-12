"""Tests for the group key-value model.

This module contains tests for the group key-value model's functionality,
including basic operations, complex data types, and data persistence.
It verifies both model attributes and data manipulation operations.
"""
from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session

from ring.parties.models.group_key_value import GroupKeyValue
from ring.tests.factories.parties.group_factory import GroupFactory


class TestGroupKeyValue:
    """Test suite for the group key-value model.

    This class contains tests for all group key-value model functionality,
    including basic operations, complex data types, and data persistence.
    """

    def test_basic_operations(self, db_session: Session):
        """Test basic group key-value operations.

        This test verifies that:
        1. A key-value pair can be set
        2. The value can be retrieved
        3. The data is properly stored in the database
        4. The data can be loaded from the database

        Args:
            db_session (Session): Database session
        """
        # Create a new key-value entry
        group = GroupFactory.create()
        group.key_values.set_value("test_key", "test_value")
        db_session.add(group)
        db_session.commit()

        # Verify the value was stored
        loaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()
        assert loaded_kv is not None
        assert loaded_kv.get_value("test_key") == "test_value"

    def test_complex_types(self, db_session: Session):
        """Test storing complex data types in group key-value store.

        This test verifies that:
        1. Dictionaries can be stored and retrieved
        2. Lists can be stored and retrieved
        3. Boolean values can be stored and retrieved
        4. Nested complex types are handled correctly
        5. All data types are properly persisted

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        db_session.add(group)
        db_session.commit()

        # Test dictionary
        group.key_values.set_value("dict_key", {"nested": {"value": 42}})

        # Test list
        group.key_values.set_value("list_key", [1, 2, 3, {"nested": "value"}])

        # Test boolean
        group.key_values.set_value("bool_key", True)

        db_session.add(group)
        db_session.commit()

        # Verify all values were stored correctly
        loaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()
        assert loaded_kv is not None
        assert loaded_kv.get_value("dict_key") == {"nested": {"value": 42}}
        assert loaded_kv.get_value("list_key") == [
            1,
            2,
            3,
            {"nested": "value"},
        ]
        assert loaded_kv.get_value("bool_key") is True

    def test_delete(self, db_session: Session):
        """Test deleting values from group key-value store.

        This test verifies that:
        1. A specific key-value pair can be deleted
        2. Other key-value pairs remain unchanged
        3. The deletion is properly persisted
        4. The deleted value returns None when retrieved

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        group.key_values.set_value("key1", "value1")
        group.key_values.set_value("key2", "value2")
        db_session.add(group)
        db_session.commit()

        # Delete one key
        loaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()

        loaded_kv.delete_value("key1")
        db_session.commit()

        # Verify key was deleted
        reloaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()
        assert reloaded_kv.get_value("key1") is None
        assert reloaded_kv.get_value("key2") == "value2"

    def test_nested_mutation(self, db_session: Session):
        """Test that nested mutations in the JSONB field are tracked correctly.

        This test verifies that:
        1. Nested data structures can be modified
        2. Changes to nested structures are tracked
        3. Changes are properly persisted
        4. The modified data can be retrieved correctly

        Args:
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        group.key_values.set_value(
            "nested", {"level1": {"level2": ["a", "b", "c"]}}
        )
        db_session.add(group)
        db_session.commit()

        # Modify nested structure
        loaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()
        nested_data = loaded_kv.get_value("nested")
        nested_data["level1"]["level2"].append("d")
        db_session.commit()

        # Verify changes were tracked and persisted
        reloaded_kv = db_session.scalars(
            sqlalchemy.select(GroupKeyValue).where(
                GroupKeyValue.group_id == group.id
            )
        ).one()
        assert reloaded_kv.get_value("nested")["level1"]["level2"] == [
            "a",
            "b",
            "c",
            "d",
        ]
