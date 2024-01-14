from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.sqlalchemy_base import Base

letter_to_user_assocation = Table(
    "letter_to_user_assocation",
    Base.metadata,
    Column("letter_id", Integer, ForeignKey("letter.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)


class Letter(Base):
    __tablename__ = "letter"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[int] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group_id = Column(Integer, ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(back_populates="letter")
    responses: Mapped[list["Response"]] = relationship(back_populates="letter")
