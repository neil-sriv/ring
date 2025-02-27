from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_json import mutable_json_type

from ring.sqlalchemy_base import Base


class ModelKeyValue(AbstractConcreteBase, Base):
    """Abstract base class for models that support key-value storage."""

    strict_attrs = True

    key_values: Mapped[dict] = mapped_column(
        mutable_json_type(dbtype=JSONB, nested=True),
        default=dict,
        nullable=False,
    )

    def set_all_values(self, key_values: Dict[str, Any]) -> None:
        """Set all key-value pairs."""
        self.key_values = key_values

    def get_value(self, key: str) -> Optional[Any]:
        """Get a value from the key-value store."""
        return self.key_values.get(key)

    def set_value(self, key: str, value: Any) -> None:
        """Set a value in the key-value store."""
        self.key_values[key] = value

    def delete_value(self, key: str) -> None:
        """Delete a value from the key-value store."""
        self.key_values.pop(key, None)

    def get_all_values(self) -> Dict[str, Any]:
        """Get all key-value pairs."""
        return dict(self.key_values)
