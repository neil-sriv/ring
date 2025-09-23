"""Document schemas for API requests and responses.

This module provides Pydantic models for document-related API operations,
including creation, updates, and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    name: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Initial content of the document")
    group_api_id: str = Field(..., description="API identifier of the group")


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    name: Optional[str] = Field(None, description="New name for the document")
    content: Optional[str] = Field(
        None, description="New content for the document"
    )


class DocumentResponse(BaseModel):
    """Schema for document responses."""

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str = Field(
        ..., description="API identifier of the document"
    )
    name: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Current content of the document")
    latest_snapshot_version: int = Field(
        ..., description="Latest snapshot version"
    )
    created_at: datetime = Field(
        ..., description="When the document was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="When the document was last updated"
    )
