"""Schemas for group key-value operations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SingleGroupKeyValueBase(BaseModel):
    """Base schema for group key-value operations."""

    key: str = Field(..., description="The key")
    value: Any = Field(..., description="The value")


class SingleGroupKeyValueUpdate(SingleGroupKeyValueBase):
    """Schema for updating a group key-value pair."""

    operation: Literal["set", "delete"] = Field(
        ..., description="The operation to perform"
    )
    value: Any | None = Field(
        None,
        description=(
            "The value to set. Required for 'set' operation, ignored for 'delete'"
        ),
    )

    @model_validator(mode="after")
    def validate_value_for_operation(self) -> "GroupKeyValueUpdate":
        """Validate that value is present for set operations."""
        if self.operation == "set" and self.value is None:
            raise ValueError("value is required for 'set' operation")
        return self


class BulkGroupKeyValueUpdate(BaseModel):
    """Schema for bulk updating multiple key-value pairs."""

    updates: list[SingleGroupKeyValueUpdate] = Field(
        ...,
        description="List of updates to perform",
        min_length=1,
    )


class GroupKeyValue(SingleGroupKeyValueBase):
    """Schema for group key-value responses."""

    model_config = ConfigDict(from_attributes=True)
