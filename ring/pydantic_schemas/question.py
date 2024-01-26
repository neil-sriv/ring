from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class QuestionBase(BaseModel):
    question_text: str


class QuestionCreate(QuestionBase):
    letter_api_identifier: str


class Question(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class QuestionUnlinked(Question):
    pass
