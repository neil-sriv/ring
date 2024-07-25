from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QuestionBase(BaseModel):
    question_text: str


class QuestionCreate(QuestionBase):
    author_api_id: str | None


class Question(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime


class QuestionUnlinked(Question):
    pass
