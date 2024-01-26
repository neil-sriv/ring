from typing import Optional
from ring.pydantic_schemas.schemas import *


class UserLinked(User):
    groups: list["GroupUnlinked"]
    responses: list["ResponseUnlinked"]


class GroupLinked(Group):
    members: list["UserUnlinked"]
    letters: list["LetterUnlinked"]
    schedule: Optional["ScheduleUnlinked"]


class ScheduleLinked(Schedule):
    group: "GroupUnlinked"
    tasks: list["TaskUnlinked"]


class TaskLinked(Task):
    schedule: "ScheduleUnlinked"


class LetterLinked(Letter):
    participants: list["UserUnlinked"]
    group: "GroupUnlinked"
    questions: list["QuestionUnlinked"]


class QuestionLinked(Question):
    letter: "LetterUnlinked"
    responses: list["ResponseUnlinked"]


class ResponseLinked(Response):
    question: "QuestionUnlinked"
    participant: "UserUnlinked"
