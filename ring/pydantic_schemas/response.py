from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict


if TYPE_CHECKING:
    from ring.pydantic_schemas.user import UserUnlinked
    from ring.pydantic_schemas.question import QuestionUnlinked


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
