from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group_api_identifier: str


class Letter(LetterBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int


class LetterUnlinked(Letter):
    pass
