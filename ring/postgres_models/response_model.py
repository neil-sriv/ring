from __future__ import annotations
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.sqlalchemy_base import Base


class Response(Base):
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participant_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    participant: Mapped["User"] = relationship()
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"))
    question: Mapped["Question"] = relationship(back_populates="responses")

    response_text: Mapped[str] = mapped_column(Text)

    letter_id: Mapped[int] = mapped_column(ForeignKey("letter.id"))
    letter: Mapped["Letter"] = relationship(back_populates="responses")
