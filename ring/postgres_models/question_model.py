from __future__ import annotations
from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.sqlalchemy_base import Base

question_to_user_association = Table(
    "question_to_user_association",
    Base.metadata,
    Column("question_id", String, ForeignKey("question.id")),
    Column("user_id", String, ForeignKey("user.id")),
)


class Question(Base, APIIdentified):
    __tablename__ = "question"

    API_ID_PREFIX = "qstn"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=question_to_user_association
    )
    responses: Mapped[list["Response"]] = relationship(
        back_populates="question",
    )

    question_text: Mapped[str] = mapped_column(Text)

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="questions")
