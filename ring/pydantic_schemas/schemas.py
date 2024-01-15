from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ResponseBase(BaseModel):
    response_text: str


class ResponseCreate(ResponseBase):
    question_api_id: str
    participant_api_id: str


class Response(ResponseBase):
    api_identifier: str
    question: "Question"
    participant: "User"

    class Config:
        orm_mode = True


class QuestionBase(BaseModel):
    question_text: str


class QuestionCreate(QuestionBase):
    letter_api_id: str


class Question(QuestionBase):
    api_identifier: str
    letter: "Letter"
    responses: list["Response"]

    class Config:
        orm_mode = True


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group_api_id: str


class Letter(LetterBase):
    api_identifier: str
    number: int
    participants: list["User"]
    group: "Group"

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    name: Optional[str] = None


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    api_identifier: str
    groups: list["Group"]
    # letters: list[Letter]

    class Config:
        orm_mode = True


class GroupBase(BaseModel):
    name: str
    admin_api_id: str


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    api_identifier: str
    admin: "User"
    members: list["User"]
    letters: list["Letter"]

    class Config:
        orm_mode = True


Response.model_rebuild()
Question.model_rebuild()
User.model_rebuild()
Group.model_rebuild()
Letter.model_rebuild()
