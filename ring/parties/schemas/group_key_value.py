"""Schemas for group key-value operations.

This module defines Pydantic models for validating and serializing group key-value
operations in the Ring API. It includes schemas for basic operations, single updates,
and bulk updates.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class GroupKeyValueBase(BaseModel):
    """Base schema for group key-value operations.

    This is the base model that defines the fundamental structure of a key-value pair.
    It is used as a building block for other key-value related schemas.

    Attributes:
        key (str): The key identifier for the value
        value (Any): The value associated with the key, can be any JSON-serializable type
    """

    key: str = Field(..., description="The key identifier for the value")
    value: Any = Field(..., description="The value associated with the key")


class GroupKeyValue(BaseModel):
    """Schema for group key-value responses.

    This model represents the complete key-value store for a group, containing
    all key-value pairs in a dictionary format.

    Attributes:
        key_values (dict[str, Any]): Dictionary containing all key-value pairs for the group
    """

    key_values: dict[str, Any] = Field(
        ..., 
        description="Dictionary containing all key-value pairs for the group"
    )


class SingleGroupKeyValueUpdate(GroupKeyValueBase):
    """Schema for updating a single group key-value pair.

    This model extends GroupKeyValueBase to include an operation field that specifies
    whether to set or delete the key-value pair.

    Attributes:
        key (str): The key identifier to update
        value (Any | None): The value to set (required for 'set' operation, ignored for 'delete')
        operation (Literal["set", "delete"]): The operation to perform on the key-value pair

    Note:
        For 'delete' operations, the value field is ignored
    """

    operation: Literal["set", "delete"] = Field(
        ..., 
        description="Operation to perform: 'set' to update/create, 'delete' to remove"
    )
    value: Any | None = Field(
        None,
        description="Value to set (required for 'set' operation, ignored for 'delete')",
    )

    @model_validator(mode='after')
    def validate_value_for_operation(self) -> 'SingleGroupKeyValueUpdate':
        """Validate that value is provided for 'set' operations.

        Returns:
            SingleGroupKeyValueUpdate: The validated model instance

        Raises:
            ValueError: If value is missing for a 'set' operation
        """
        if self.operation == "set" and self.value is None:
            raise ValueError("Value must be provided for 'set' operation")
        return self


class BulkGroupKeyValueUpdate(BaseModel):
    """Schema for bulk updating multiple key-value pairs.

    This model allows multiple key-value operations to be performed in a single request.
    Each update in the list can be either a 'set' or 'delete' operation.

    Attributes:
        updates (list[SingleGroupKeyValueUpdate]): List of update operations to perform

    Note:
        At least one update operation must be provided
    """

    updates: list[SingleGroupKeyValueUpdate] = Field(
        ...,
        description="List of key-value update operations to perform",
        min_length=1,
    )
