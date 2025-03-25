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

    :param strict_attrs: Whether to enforce strict attribute access
    :type strict_attrs: bool
    :param key_values: Dictionary storing the key-value pairs
    :type key_values: Mapped[dict]
    :ivar key_values: JSONB column with mutable dictionary support, non-nullable, defaults to empty dict
    """

    strict_attrs = True

    key_values: Mapped[dict] = mapped_column(
        mutable_json_type(dbtype=JSONB, nested=True),
        default=dict,
        nullable=False,
    )

    def set_all_values(self, key_values: Dict[str, Any]) -> None:
        """Replace all existing key-value pairs with a new dictionary.

        :param key_values: Dictionary containing new key-value pairs to store
        :type key_values: Dict[str, Any]
        :return: None
        :rtype: None
        """
        self.key_values = key_values

    def get_value(self, key: str) -> Optional[Any]:
        """Retrieve a value from the key-value store by its key.

        :param key: Key to look up
        :type key: str
        :return: Value associated with the key if it exists, None otherwise
        :rtype: Optional[Any]
        """
        return self.key_values.get(key)

    def set_value(self, key: str, value: Any) -> None:
        """Store a value in the key-value store with the given key.

        :param key: Key under which to store the value
        :type key: str
        :param value: Value to store
        :type value: Any
        :return: None
        :rtype: None
        """
        self.key_values[key] = value

    def delete_value(self, key: str) -> None:
        """Remove a key-value pair from the store if it exists.

        :param key: Key to remove
        :type key: str
        :return: None
        :rtype: None
        """
        self.key_values.pop(key, None)

    def get_all_values(self) -> Dict[str, Any]:
        """Retrieve all key-value pairs as a dictionary.

        :return: Dictionary containing all stored key-value pairs
        :rtype: Dict[str, Any]
        """
        return dict(self.key_values)
