from __future__ import annotations
from sqlalchemy import Column, ForeignKey, String, Integer, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.fast import Base

letter_to_user_assocation = Table(
    "letter_to_user_assocation",
    Base.metadata,
    Column("letter_api_id", String, ForeignKey("letters.api_identifier")),
    Column("user_api_id", String, ForeignKey("users.api_identifier")),
)


class Letter(Base):
    __tablename__ = "letter"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[Integer] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[String] = mapped_column(unique=True, index=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(back_populates="letter")
    responses: Mapped[list["Response"]] = relationship(back_populates="letter")
