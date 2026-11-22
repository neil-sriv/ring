"""CRUD operations for group key-value store.

This module provides functions for managing a key-value store associated with
each group, allowing for flexible storage of group-specific settings and data.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.letters.send_threshold import APP_CONTROLLED_GROUP_KEYS
from ring.parties.models.group_key_value import GroupKeyValue
from ring.parties.models.group_model import Group


class ReservedGroupKey(Exception):
    """A store write targeted an app-controlled group setting."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)


def _reject_reserved_keys(keys: Iterable[str]) -> None:
    for key in keys:
        if key in APP_CONTROLLED_GROUP_KEYS:
            raise ReservedGroupKey(key)


def _visible_values(key_values: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in key_values.items()
        if key not in APP_CONTROLLED_GROUP_KEYS
    }


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
    if key in APP_CONTROLLED_GROUP_KEYS:
        return None
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

    Raises:
        ReservedGroupKey: If key is an app-controlled setting
    """
    _reject_reserved_keys([key])
    kv = _get_group_key_value(db, group)
    kv.set_value(key, value)


def delete_value(db: Session, group: Group, key: str) -> None:
    """Delete a value from a group's key-value store.

    Args:
        db (Session): Database session
        group (Group): Group to delete value from
        key (str): Key to delete

    Raises:
        ReservedGroupKey: If key is an app-controlled setting
    """
    _reject_reserved_keys([key])
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
    return _visible_values(kv.get_all_values())


def merge_values(
    db: Session, group: Group, key_values: dict[str, Any]
) -> None:
    """Upsert the given keys, leaving every other key in place.

    A full-replace body is the caller's snapshot. Keys they never loaded
    are absent from that snapshot and must survive. App-setting keys are
    dropped from the stored dict so a later save cannot keep them around.

    Args:
        db (Session): Database session
        group (Group): Group to update
        key_values (dict[str, Any]): Keys to insert or overwrite

    Raises:
        ReservedGroupKey: If key_values contains an app-controlled setting
    """
    _reject_reserved_keys(key_values)
    kv = _get_group_key_value(db, group)
    merged = _visible_values(kv.get_all_values())
    merged.update(key_values)
    kv.set_all_values(merged)
