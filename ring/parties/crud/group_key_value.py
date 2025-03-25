"""CRUD operations for group key-value store."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.group_key_value import GroupKeyValue
from ring.parties.models.group_model import Group


def _get_group_key_value(db: Session, group: Group) -> GroupKeyValue:
    """Get the key-value store for a group.

    :param db: Database session
    :type db: Session
    :param group: Group to get key-value store for
    :type group: Group
    :return: Group's key-value store
    :rtype: GroupKeyValue
    :raises sqlalchemy.exc.NoResultFound: If no key-value store exists for the group
    """
    return db.scalars(
        select(GroupKeyValue).where(GroupKeyValue.group_id == group.id)
    ).one()


def get_value(db: Session, group: Group, key: str) -> Any:
    """Get a value from a group's key-value store.

    :param db: Database session
    :type db: Session
    :param group: Group to get value from
    :type group: Group
    :param key: Key to retrieve
    :type key: str
    :return: Value associated with the key, or None if not found
    :rtype: Any
    """
    kv = _get_group_key_value(db, group)
    if kv is None:
        return None
    return kv.get_value(key)


def set_value(db: Session, group: Group, key: str, value: Any) -> None:
    """Set a value in a group's key-value store.

    :param db: Database session
    :type db: Session
    :param group: Group to set value for
    :type group: Group
    :param key: Key to set
    :type key: str
    :param value: Value to store
    :type value: Any
    """
    kv = _get_group_key_value(db, group)
    kv.set_value(key, value)


def delete_value(db: Session, group: Group, key: str) -> None:
    """Delete a value from a group's key-value store.

    :param db: Database session
    :type db: Session
    :param group: Group to delete value from
    :type group: Group
    :param key: Key to delete
    :type key: str
    """
    kv = _get_group_key_value(db, group)
    kv.delete_value(key)


def get_all_values(db: Session, group: Group) -> dict[str, Any]:
    """Get all values from a group's key-value store.

    :param db: Database session
    :type db: Session
    :param group: Group to get values from
    :type group: Group
    :return: Dictionary of all key-value pairs
    :rtype: dict[str, Any]
    """
    kv = _get_group_key_value(db, group)
    return kv.get_all_values()


def set_all_values(
    db: Session, group: Group, key_values: dict[str, Any]
) -> None:
    """Set all key-value pairs in a group's key-value store.

    :param db: Database session
    :type db: Session
    :param group: Group to set values for
    :type group: Group
    :param key_values: Dictionary of key-value pairs to set
    :type key_values: dict[str, Any]
    """
    kv = _get_group_key_value(db, group)
    kv.set_all_values(key_values)
