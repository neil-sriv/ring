from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict


if TYPE_CHECKING:
    from ring.pydantic_schemas.letter import LetterUnlinked
    from ring.pydantic_schemas.response import ResponseUnlinked


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
