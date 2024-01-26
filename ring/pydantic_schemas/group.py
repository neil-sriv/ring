from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict
from ring.pydantic_schemas.user import UserUnlinked
from ring.pydantic_schemas.schedule import ScheduleUnlinked
from ring.pydantic_schemas.letter import LetterUnlinked


class GroupBase(BaseModel):
    name: str
    admin: "UserUnlinked"


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class GroupLinked(Group):
    members: list["UserUnlinked"]
    letters: list["LetterUnlinked"]
    schedule: Optional["ScheduleUnlinked"] = None


class GroupUnlinked(Group):
    pass
