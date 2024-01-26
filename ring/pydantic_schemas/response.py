from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class ResponseBase(BaseModel):
    response_text: str


class ResponseCreate(ResponseBase):
    question_api_identifier: str
    participant_api_identifier: str


class Response(ResponseBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class ResponseUnlinked(Response):
    pass
