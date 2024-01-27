from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.letter_model import Letter

    # from ring.postgres_models.user_model import User
    from ring.postgres_models.response_model import Response

question_to_user_association = Table(
    "question_to_user_association",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("question.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)


class Question(Base, APIIdentified):
    __tablename__ = "question"

    API_ID_PREFIX = "qstn"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    # participants: Mapped[list["User"]] = relationship(
    #     secondary=question_to_user_association
    # )
    responses: Mapped[list["Response"]] = relationship(
        back_populates="question",
    )

    question_text: Mapped[str] = mapped_column(Text)

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="questions")

    def __init__(self, letter: Letter, question_text: str) -> None:
        APIIdentified.__init__(self)
        self.letter = letter
        self.question_text = question_text
        # self.participants = []

    @classmethod
    def create(cls, letter: Letter, question_text: str) -> Question:
        question = cls(letter, question_text)
        return question
