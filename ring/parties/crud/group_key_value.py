"""CRUD operations for group key-value store.

This module provides functions for managing a key-value store associated with
each group, allowing for flexible storage of group-specific settings and data.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.group_key_value import GroupKeyValue
from ring.parties.models.group_model import Group


def _get_group_key_value(db: Session, group: Group) -> GroupKeyValue:
    """Get the key-value store for a group.

    Args:
        db (Session): Database session
        group (Group): Group to get key-value store for

    Returns:
        GroupKeyValue: Group's key-value store

    Raises:
        sqlalchemy.exc.NoResultFound: If no key-value store exists for the group
    """
    return db.scalars(
        select(GroupKeyValue).where(GroupKeyValue.group_id == group.id)
    ).one()


def get_value(db: Session, group: Group, key: str) -> Any:
    """Get a value from a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to get value from
        key (str): Key to retrieve

    Returns:
        Any: Value associated with the key, or None if not found
    """
    kv = _get_group_key_value(db, group)
    if kv is None:
        return None
    return kv.get_value(key)


def set_value(db: Session, group: Group, key: str, value: Any) -> None:
    """Set a value in a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to set value for
        key (str): Key to set
        value (Any): Value to store
    """
    kv = _get_group_key_value(db, group)
    kv.set_value(key, value)


def delete_value(db: Session, group: Group, key: str) -> None:
    """Delete a value from a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to delete value from
        key (str): Key to delete
    """
    kv = _get_group_key_value(db, group)
    kv.delete_value(key)


def get_all_values(db: Session, group: Group) -> dict[str, Any]:
    """Get all values from a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to get values from

    Returns:
        dict[str, Any]: Dictionary of all key-value pairs
    """
    kv = _get_group_key_value(db, group)
    return kv.get_all_values()


def set_all_values(
    db: Session, group: Group, key_values: dict[str, Any]
) -> None:
    """Set all key-value pairs in a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to set values for
        key_values (dict[str, Any]): Dictionary of key-value pairs to set
    """
    kv = _get_group_key_value(db, group)
    kv.set_all_values(key_values)
