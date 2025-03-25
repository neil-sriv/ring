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
    """SQLAlchemy model representing a letter in the system.

    A letter is a collection of questions sent to a group of participants at a specific time.
    It tracks the status, participants, and associated responses.

    :param id: Primary key identifier
    :type id: Mapped[int]
    :param number: Sequential number of the letter within its group
    :type number: Mapped[int]
    :param api_identifier: Unique API identifier for the letter
    :type api_identifier: Mapped[str]
    :param status: Current status of the letter
    :type status: Mapped[str]
    :param send_at: Scheduled send time of the letter
    :type send_at: Mapped[datetime]
    :param participants: List of users participating in the letter
    :type participants: Mapped[list[User]]
    :param group: Group to which the letter belongs
    :type group: Mapped[Group]
    :param questions: List of questions in the letter
    :type questions: Mapped[list[Question]]
    """

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
        """Define table constraints.

        :return: Tuple of table constraints
        :rtype: tuple[Constraint]
        """
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
        """Initialize a new Letter instance.

        :param group: Group to which the letter belongs
        :type group: Group
        :param send_at: Scheduled send time of the letter
        :type send_at: datetime
        :param status: Initial status of the letter
        :type status: LetterStatus
        :param number: Optional letter number, defaults to None
        :type number: int | None
        :return: None
        :rtype: None
        """
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
        """Create a new Letter instance.

        Factory method to create a new letter with the given parameters.

        :param group: Group to which the letter belongs
        :type group: Group
        :param send_at: Scheduled send time of the letter
        :type send_at: datetime
        :param letter_status: Initial status of the letter
        :type letter_status: LetterStatus
        :param number: Optional letter number, defaults to None
        :type number: int | None
        :return: New Letter instance
        :rtype: Letter
        """
        letter = cls(group, send_at, letter_status, number=number)
        return letter

    @hybrid_property
    def responders(self) -> list[User]:
        """Get list of users who have responded to any question in the letter.

        :return: List of users who have submitted responses
        :rtype: list[User]
        """
        respondents = {
            response.participant
            for question in self.questions
            for response in question.responses
        }
        return list(respondents)
