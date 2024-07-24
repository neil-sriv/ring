from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    admin_api_identifier: str


class GroupUpdate(BaseModel):
    name: str | None = None


class Group(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class GroupUnlinked(Group):
    pass
