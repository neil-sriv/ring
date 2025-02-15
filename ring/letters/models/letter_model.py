from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Constraint,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.letters.constants import LetterStatus
from ring.letters.models.question_model import Question
from ring.ring_pydantic.linked_schemas import PublicLetter
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.group_model import Group
    from ring.parties.models.user_model import User

letter_to_user_assocation = Table(
    "letter_to_user_assocation",
    Base.metadata,
    Column("letter_id", Integer, ForeignKey("letter.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)


class Letter(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    __tablename__ = "letter"

    API_ID_PREFIX = "lttr"
    PYDANTIC_MODEL = PublicLetter

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[int] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[str] = mapped_column()
    send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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

    def __init__(
        self,
        group: Group,
        send_at: datetime,
        status: LetterStatus,
        number: int | None = None,
    ) -> None:
        APIIdentified.__init__(self)
        self.number = number if number else len(group.letters) + 1
        self.group = group
        self.participants = group.members
        self.send_at = send_at
        self.status = status

    @classmethod
    def create(
        cls,
        group: Group,
        send_at: datetime,
        letter_status: LetterStatus,
        number: int | None = None,
    ) -> Letter:
        letter = cls(group, send_at, letter_status, number=number)
        return letter

    @hybrid_property
    def responders(self) -> list[User]:
        respondents = {
            response.participant
            for question in self.questions
            for response in question.responses
        }
        return list(respondents)
