from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ResponseBase(BaseModel):
    response_text: str


class ResponseCreateBase(ResponseBase):
    pass


class ResponseUpsert(ResponseCreateBase):
    participant_api_identifier: Optional[str] = None
    api_identifier: Optional[str] = None


class ResponseCreate(ResponseCreateBase):
    question_api_identifier: str
    participant_api_identifier: str


class Response(ResponseBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime


class ResponseUnlinked(Response):
    pass
