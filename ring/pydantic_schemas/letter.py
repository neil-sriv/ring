from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict


if TYPE_CHECKING:
    from ring.pydantic_schemas.user import UserUnlinked
    from ring.pydantic_schemas.group import GroupUnlinked
    from ring.pydantic_schemas.question import QuestionUnlinked


class LetterBase(BaseModel):
    pass


class LetterCreate(LetterBase):
    group: "GroupUnlinked"


class Letter(LetterBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int


class LetterLinked(Letter):
    participants: list["UserUnlinked"]
    group: "GroupUnlinked"
    questions: list["QuestionUnlinked"]


class LetterUnlinked(Letter):
    pass
