"""Pydantic schemas for in-app inbox items."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InboxItemResponse(BaseModel):
    """One inbox row as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    title: str
    body: str
    target_api_id: str | None
    href: str
    read_at: datetime | None
    created_at: datetime
    unread: bool


class InboxUnreadCount(BaseModel):
    """Unread total for the current user."""

    unread_count: int
