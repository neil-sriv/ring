from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from ring.api_identifier.api_identified_model import APIIdentified

from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import QuestionLinked
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter

    from ring.letters.models.response_model import Response


class Question(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    __tablename__ = "question"

    API_ID_PREFIX = "qstn"
    PYDANTIC_MODEL = QuestionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    responses: Mapped[list["Response"]] = relationship(
        back_populates="question", cascade="all"
    )

    question_text: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=True, default=None
    )
    author: Mapped["User | None"] = relationship()

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="questions")

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
