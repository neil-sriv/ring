from typing import Optional
from pydantic import BaseModel, ConfigDict


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
    schedule: Optional["ScheduleUnlinked"]


class GroupUnlinked(Group):
    pass


class ScheduleBase(BaseModel):
    pass


class ScheduleCreate(ScheduleBase):
    group: "GroupUnlinked"


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class ScheduleLinked(Schedule):
    group: "GroupUnlinked"


class ScheduleUnlinked(Schedule):
    pass


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group: "GroupUnlinked"


class Letter(LetterBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int


class LetterLinked(Letter):
    participants: list["UserUnlinked"]
    group: "GroupUnlinked"
    questions: list["QuestionUnlinked"]


class LetterUnlinked(Letter):
    pass


class QuestionBase(BaseModel):
    question_text: str


class QuestionCreate(QuestionBase):
    letter: "LetterUnlinked"


class Question(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class QuestionLinked(Question):
    letter: "LetterUnlinked"
    responses: list["ResponseUnlinked"]


class QuestionUnlinked(Question):
    pass


class ResponseBase(BaseModel):
    response_text: str


class ResponseCreate(ResponseBase):
    question: "QuestionUnlinked"
    participant: "UserUnlinked"


class Response(ResponseBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class ResponseLinked(Response):
    question: "QuestionUnlinked"
    participant: "UserUnlinked"


class ResponseUnlinked(Response):
    pass
