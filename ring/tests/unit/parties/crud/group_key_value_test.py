"""Tests for group key-value CRUD operations."""

import sqlalchemy

from ring.parties.crud.group_key_value import (
    delete_value,
    get_all_values,
    get_value,
    set_value,
)
from ring.tests.factories.parties.group_factory import GroupFactory


def test_get_value(db_session):
    """Test getting a value from a group's key-value store."""
    group = GroupFactory.create()
    db_session.add(group)
    db_session.commit()

    # Test getting non-existent value
    assert get_value(db_session, group, "test_key") is None

    # Test getting existing value
    set_value(db_session, group, "test_key", "test_value")
    assert get_value(db_session, group, "test_key") == "test_value"


def test_set_value(db_session):
    """Test setting values in a group's key-value store."""
    group = GroupFactory.create()
    db_session.add(group)
    db_session.commit()

    # Test setting simple value
    set_value(db_session, group, "string_key", "test_value")
    assert get_value(db_session, group, "string_key") == "test_value"

    # Test setting complex value
    complex_value = {
        "nested": {"value": 42},
        "list": [1, 2, {"nested": "value"}],
    }
    set_value(db_session, group, "complex_key", complex_value)
    assert get_value(db_session, group, "complex_key") == complex_value


def test_delete_value(db_session):
    """Test deleting values from a group's key-value store."""
    group = GroupFactory.create()
    db_session.add(group)
    db_session.commit()

    # Set up test values
    set_value(db_session, group, "key1", "value1")
    set_value(db_session, group, "key2", "value2")

    # Delete one value
    delete_value(db_session, group, "key1")
    assert get_value(db_session, group, "key1") is None
    assert get_value(db_session, group, "key2") == "value2"


def test_get_all_values(db_session):
    """Test getting all values from a group's key-value store."""
    group = GroupFactory.create()
    db_session.add(group)
    db_session.commit()

    # Test empty store
    assert get_all_values(db_session, group) == {}

    # Add some values
    test_values = {
        "key1": "value1",
        "key2": 42,
        "key3": {"nested": "value"},
    }
    for key, value in test_values.items():
        set_value(db_session, group, key, value)

    # Test getting all values
    assert get_all_values(db_session, group) == test_values
