from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class UserUnlinked(User):
    pass
