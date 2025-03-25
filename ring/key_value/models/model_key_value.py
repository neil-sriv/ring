"""Key-value storage model for SQLAlchemy.

This module provides an abstract base class for models that support flexible
key-value storage using PostgreSQL's JSONB type. Inheriting models can store
arbitrary key-value pairs in a single column.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_json import mutable_json_type

from ring.sqlalchemy_base import Base


class ModelKeyValue(AbstractConcreteBase, Base):
    """Abstract base class for models that support key-value storage.

    Provides a flexible key-value storage mechanism using PostgreSQL's JSONB type.
    Inheriting models can store arbitrary key-value pairs in a single column.

    Attributes:
        strict_attrs (bool): Whether to enforce strict attribute access
        key_values (Mapped[dict]): JSONB column with mutable dictionary support,
            non-nullable, defaults to empty dict
    """

    strict_attrs = True

    key_values: Mapped[dict] = mapped_column(
        mutable_json_type(dbtype=JSONB, nested=True),
        default=dict,
        nullable=False,
    )

    def set_all_values(self, key_values: Dict[str, Any]) -> None:
        """Replace all existing key-value pairs with a new dictionary.

        Args:
            key_values (Dict[str, Any]): Dictionary containing new key-value pairs to store
        """
        self.key_values = key_values

    def get_value(self, key: str) -> Optional[Any]:
        """Retrieve a value from the key-value store by its key.

        Args:
            key (str): Key to look up

        Returns:
            Optional[Any]: Value associated with the key if it exists, None otherwise
        """
        return self.key_values.get(key)

    def set_value(self, key: str, value: Any) -> None:
        """Store a value in the key-value store with the given key.

        Args:
            key (str): Key under which to store the value
            value (Any): Value to store
        """
        self.key_values[key] = value

    def delete_value(self, key: str) -> None:
        """Remove a key-value pair from the store if it exists.

        Args:
            key (str): Key to remove
        """
        self.key_values.pop(key, None)

    def get_all_values(self) -> Dict[str, Any]:
        """Retrieve all key-value pairs as a dictionary.

        Returns:
            Dict[str, Any]: Dictionary containing all stored key-value pairs
        """
        return dict(self.key_values)
