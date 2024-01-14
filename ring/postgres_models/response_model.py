from __future__ import annotations
from sqlalchemy import String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.fast import Base


class Response(Base):
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_identifier: Mapped[String] = mapped_column(unique=True, index=True)

    participant: Mapped["User"] = relationship(back_populates="response")
    question: Mapped["Question"] = relationship(back_populates="responses")

    response_text: Mapped[Text] = mapped_column()
