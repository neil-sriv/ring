from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class UserUnlinked(User):
    pass


class NewPassword(BaseModel):
    new_password: str
    token: str
