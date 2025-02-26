"""Schemas for group key-value operations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class GroupKeyValueBase(BaseModel):
    """Base schema for group key-value operations."""

    key: str = Field(..., description="The key")
    value: Any = Field(..., description="The value")


class GroupKeyValue(BaseModel):
    """Schema for group key-value responses."""

    key_values: dict[str, Any] = Field(..., description="The key-values")


class SingleGroupKeyValueUpdate(GroupKeyValueBase):
    """Schema for updating a group key-value pair."""

    operation: Literal["set", "delete"] = Field(
        ..., description="The operation to perform"
    )
    value: Any | None = Field(
        None,
        description=("The value to set. Ignored for 'delete'"),
    )


class BulkGroupKeyValueUpdate(BaseModel):
    """Schema for bulk updating multiple key-value pairs."""

    updates: list[SingleGroupKeyValueUpdate] = Field(
        ...,
        description="List of updates to perform",
        min_length=1,
    )
