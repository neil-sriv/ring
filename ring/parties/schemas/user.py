from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class UserBase(BaseModel):
    email: str
    name: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: str) -> str:
        return email.lower()


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None


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
