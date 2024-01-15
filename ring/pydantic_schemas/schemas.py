from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group: Group


class Letter(LetterBase):
    api_identifier: str
    number: int
    participants: list[User]

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    name: Optional[str] = None


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    api_identifier: str
    groups: list[Group]
    # letters: list[Letter]

    class Config:
        orm_mode = True


class GroupBase(BaseModel):
    pass


class GroupCreate(GroupBase):
    members: list[User]


class Group(GroupBase):
    api_identifier: str
    name: str
    letters: list[Letter]

    class Config:
        orm_mode = True


Letter.model_rebuild()
User.model_rebuild()
Group.model_rebuild()
