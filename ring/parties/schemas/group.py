from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    admin_api_identifier: str


class GroupUpdate(BaseModel):
    name: str | None = None


class AddMembers(BaseModel):
    member_emails: list[str]


class ReplaceDefaultQuestions(BaseModel):
    questions: list[str]


class Group(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime


class GroupUnlinked(Group):
    pass
