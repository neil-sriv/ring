"""CRUD operations for group key-value store."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.group_key_value import GroupKeyValue
from ring.parties.models.group_model import Group


def _get_group_key_value(db: Session, group: Group) -> GroupKeyValue:
    """Get the key-value store for a group."""
    return db.scalars(
        select(GroupKeyValue).where(GroupKeyValue.group_id == group.id)
    ).one()


def get_value(db: Session, group: Group, key: str) -> Any:
    """Get a value from a group's key-value store."""
    kv = _get_group_key_value(db, group)
    if kv is None:
        return None
    return kv.get_value(key)


def set_value(db: Session, group: Group, key: str, value: Any) -> None:
    """Set a value in a group's key-value store."""
    kv = _get_group_key_value(db, group)
    kv.set_value(key, value)
    db.commit()


def delete_value(db: Session, group: Group, key: str) -> None:
    """Delete a value from a group's key-value store."""
    kv = _get_group_key_value(db, group)
    kv.delete_value(key)
    db.commit()


def get_all_values(db: Session, group: Group) -> dict[str, Any]:
    """Get all values from a group's key-value store."""
    kv = _get_group_key_value(db, group)
    return kv.get_all_values()
