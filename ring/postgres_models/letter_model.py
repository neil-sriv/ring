from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.postgres_models.api_identified import APIIdentified

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.group_model import Group
    from ring.postgres_models.question_model import Question

    # from ring.postgres_models.response_model import Response
    from ring.postgres_models.user_model import User

letter_to_user_assocation = Table(
    "letter_to_user_assocation",
    Base.metadata,
    Column("letter_id", Integer, ForeignKey("letter.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)


class Letter(Base, APIIdentified):
    __tablename__ = "letter"

    API_ID_PREFIX = "lttr"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[int] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group_id = Column(Integer, ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(back_populates="letter")
    # responses: Mapped[list["Response"]] = relationship(back_populates="letter")

    def __init__(self, group: Group) -> None:
        APIIdentified.__init__(self)
        self.group = group
        self.number = len(group.letters) + 1
        self.participants = group.members

    @classmethod
    def create(cls, group: Group) -> Letter:
        letter = cls(group)
        return letter
