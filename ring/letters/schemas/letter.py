from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ring.letters.constants import LetterStatus


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group_api_identifier: str
    send_at: datetime


class LetterUpdate(LetterBase):
    send_at: datetime


class Letter(LetterBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int
    status: LetterStatus
    send_at: datetime
    created_at: datetime


class LetterUnlinked(Letter):
    pass
