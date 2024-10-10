
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.api_identifier.api_identified_model import APIIdentified

from ring.created_at import CreatedAtMixin
from ring.parties.models.group_model import Group
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter


class DefaultQuestion(Base, APIIdentified, CreatedAtMixin):
    __tablename__ = "default_question"

    API_ID_PREFIX = "dfqstn"
    # PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    question_text: Mapped[str] = mapped_column(Text)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="default_questions")

    def __init__(
        self,
        letter: Letter,
        question_text: str,
        group: Group,
    ) -> None:
        APIIdentified.__init__(self)
        self.letter = letter
        self.question_text = question_text
        self.group = group

    @classmethod
    def create(
        cls, letter: Letter, question_text: str, group: Group
    ) -> DefaultQuestion:
        default_question = cls(letter, question_text, group)
        return default_question
