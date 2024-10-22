from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class DefaultQuestionBase(BaseModel):
    question: str


class DefaultQuestion(DefaultQuestionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class DefaultQuestionUnlinked(DefaultQuestion):
    pass
