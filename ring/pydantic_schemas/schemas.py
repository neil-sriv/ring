from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


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


class GroupCreate(GroupBase):
    admin_api_identifier: str


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
    group_api_identifier: str


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)


class ScheduleLinked(Schedule):
    group: "GroupUnlinked"
    tasks: list["TaskUnlinked"]


class ScheduleUnlinked(Schedule):
    pass


class TaskBase(BaseModel):
    pass


class TaskCreate(TaskBase):
    schedule_api_identifier: str


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    type: str
    status: str
    execute_at: datetime


class TaskLinked(Task):
    schedule: "ScheduleUnlinked"


class TaskUnlinked(Task):
    pass


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group_api_identifier: str


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
    letter_api_identifier: str


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
    question_api_identifier: str
    participant_api_identifier: str


class Response(ResponseBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class ResponseLinked(Response):
    question: "QuestionUnlinked"
    participant: "UserUnlinked"


class ResponseUnlinked(Response):
    pass
