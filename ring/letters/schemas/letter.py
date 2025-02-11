from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.letters.constants import LetterStatus


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group_api_identifier: str
    send_at: AwareDatetime


class LetterUpdate(LetterBase):
    send_at: AwareDatetime


class Letter(LetterBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int
    status: LetterStatus
    send_at: AwareDatetime
    created_at: AwareDatetime


class LetterUnlinked(Letter):
    pass
