from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    admin_api_identifier: str


class GroupUpdate(BaseModel):
    name: str | None = None


class AddMembers(BaseModel):
    member_emails: list[str]


class Group(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime


class GroupUnlinked(Group):
    pass
