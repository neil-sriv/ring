
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from ring.api_identifier.api_identified_model import APIIdentified

from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.parties.models.user_model import User
from ring.parties.models.group_model import Group
from ring.ring_pydantic.linked_schemas import QuestionLinked
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter

    from ring.letters.models.response_model import Response


# class DefaultQuestion(Base, APIIdentified, PydanticModel, CreatedAtMixin):
class DefaultQuestion(Base, CreatedAtMixin):
    __tablename__ = "default_question"

    # API_ID_PREFIX = "qstn"
    # PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    question_text: Mapped[str] = mapped_column(Text)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="default_questions")

    def __init__(
        self,
        letter: Letter,
        question_text: str,
        author: User | None,
    ) -> None:
        APIIdentified.__init__(self)
        self.letter = letter
        self.question_text = question_text
        self.author = author

    @classmethod
    def create(
        cls, letter: Letter, question_text: str, author: User | None = None
    ) -> Question:
        question = cls(letter, question_text, author)
        return question

    @hybrid_property
    def responders(self) -> list[User]:
        respondents = {response.participant for response in self.responses}
        return list(respondents)
