from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from ring.pydantic_schemas.group import GroupUnlinked
    from ring.pydantic_schemas.response import ResponseUnlinked


class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class UserLinked(User):
    groups: list["GroupUnlinked"]
    responses: list["ResponseUnlinked"]


class UserUnlinked(User):
    pass
