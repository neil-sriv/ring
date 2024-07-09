from __future__ import annotations
from typing import Optional

from ring.pydantic_schemas.image import WithImageMixin
from ring.pydantic_schemas.task import TaskUnlinked
from ring.pydantic_schemas.schedule import Schedule, ScheduleUnlinked
from ring.pydantic_schemas.user import User, UserUnlinked
from ring.pydantic_schemas.group import Group, GroupUnlinked
from ring.pydantic_schemas.letter import Letter, LetterUnlinked
from ring.pydantic_schemas.question import Question, QuestionUnlinked
from ring.pydantic_schemas.response import Response, ResponseUnlinked


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


# class TaskLinked(Task):
#     schedule: "ScheduleUnlinked"


class LetterLinked(Letter):
    participants: list["UserUnlinked"]
    group: "GroupUnlinked"
    questions: list["QuestionLinked"]


class PublicLetter(Letter):
    group: "GroupUnlinked"
    questions: list["PublicQuestion"]


class QuestionLinked(Question):
    letter: "LetterUnlinked"
    responses: list["ResponseUnlinked"]


class PublicQuestion(Question):
    responses: list["ResponseWithParticipant"]


class ResponseLinked(Response, WithImageMixin):
    question: "QuestionUnlinked"
    participant: "UserUnlinked"


class ResponseWithParticipant(Response, WithImageMixin):
    participant: "UserUnlinked"
