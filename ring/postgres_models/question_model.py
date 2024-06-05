from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.postgres_models.user_model import User
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.letter_model import Letter

    # from ring.postgres_models.user_model import User
    from ring.postgres_models.response_model import Response


class Question(Base, APIIdentified):
    __tablename__ = "question"

    API_ID_PREFIX = "qstn"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    responses: Mapped[list["Response"]] = relationship(
        back_populates="question",
    )

    question_text: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=True, default=None
    )
    author: Mapped["User"] = relationship(back_populates="authored_questions")

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="questions")

    def __init__(self, letter: Letter, question_text: str) -> None:
        APIIdentified.__init__(self)
        self.letter = letter
        self.question_text = question_text

    @classmethod
    def create(cls, letter: Letter, question_text: str) -> Question:
        question = cls(letter, question_text)
        return question
