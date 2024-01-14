from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.letter_model import Letter
    from ring.postgres_models.user_model import User
    from ring.postgres_models.question_model import Question


class Response(Base, APIIdentified):
    __tablename__ = "response"

    API_ID_PREFIX = "rspn"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participant_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    participant: Mapped["User"] = relationship()
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"))
    question: Mapped["Question"] = relationship(back_populates="responses")

    response_text: Mapped[str] = mapped_column(Text)

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="responses")
