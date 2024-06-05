from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import (
    Column,
    Constraint,
    ForeignKey,
    Integer,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from ring.postgres_models.api_identified import APIIdentified

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.group_model import Group
    from ring.postgres_models.question_model import Question

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
    number: Mapped[int] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    # TODO: Add columns for status and issue_sent datetime

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group_id = Column(Integer, ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(back_populates="letter")

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple[Constraint]:
        return (
            UniqueConstraint(
                "group_id",
                "number",
                name="unique_group_letter_number",
            ),
        )

    def __init__(self, group: Group) -> None:
        APIIdentified.__init__(self)
        self.number = len(group.letters) + 1
        self.group = group
        self.participants = group.members

    @classmethod
    def create(cls, group: Group) -> Letter:
        letter = cls(group)
        return letter
