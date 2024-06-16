from __future__ import annotations
from pydantic import BaseModel, ConfigDict

from ring.pydantic_schemas.response import ResponseUnlinked


class QuestionBase(BaseModel):
    question_text: str


class QuestionCreate(QuestionBase):
    pass


class Question(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    # responses: list["ResponseUnlinked"]


class QuestionUnlinked(Question):
    pass
