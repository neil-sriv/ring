from __future__ import annotations
from datetime import datetime
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
from ring.letter.enums import LetterStatus
from ring.postgres_models.api_identified import APIIdentified

from ring.postgres_models.pydantic_model import PydanticModel
from ring.pydantic_schemas.linked_schemas import LetterLinked
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


class Letter(Base, APIIdentified, PydanticModel):
    __tablename__ = "letter"

    API_ID_PREFIX = "lttr"
    PYDANTIC_MODEL = LetterLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[int] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[str] = mapped_column()
    issue_sent: Mapped[datetime] = mapped_column(nullable=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group_id = Column(Integer, ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(
        back_populates="letter", cascade="all"
    )

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple[Constraint]:
        return (
            UniqueConstraint(
                "group_id",
                "number",
                name="unique_group_letter_number",
            ),
        )

    def __init__(self, group: Group, status: LetterStatus) -> None:
        APIIdentified.__init__(self)
        self.number = len(group.letters) + 1
        self.group = group
        self.participants = group.members
        self.status = status

    @classmethod
    def create(cls, group: Group, letter_status: LetterStatus) -> Letter:
        letter = cls(group, letter_status)
        return letter
