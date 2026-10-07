"""SQLAlchemy model for letter management.

This module defines the Letter model, which represents a collection of questions
sent to a group of participants at a specific time. It includes functionality for
tracking status, participants, and associated responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.letters.constants import LetterStatus, LetterType
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


def next_cyclic_letter_number(group: Group) -> int:
    """Return the next unused cyclic letter number for a group.

    Numbers can have gaps (a letter skipped or inserted with an explicit
    number), so this is ``max(existing) + 1``, not ``count + 1``. Using the
    count collides with ``unique_group_letter_number`` when a gap exists.
    """
    numbers = [
        letter.number
        for letter in group.cyclic_letters
        if letter.number is not None
    ]
    return (max(numbers) if numbers else 0) + 1


@register_api_class(APIPrefix.LETTER)
class Letter(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a letter in the system.

    A letter is a collection of questions sent to a group of participants at a specific time.
    It tracks the status, participants, and associated responses.

    Attributes:
        id (Mapped[int]): Primary key identifier
        number (Mapped[int]): Sequential number of the letter within its group
        api_identifier (Mapped[str]): Unique API identifier for the letter
        status (Mapped[str]): Current status of the letter
        send_at (Mapped[datetime]): Scheduled send time of the letter
        participants (Mapped[list[User]]): List of users participating in the letter
        group (Mapped[Group]): Group to which the letter belongs
        questions (Mapped[list[Question]]): List of questions in the letter
    """

    __tablename__ = "letter"

    API_ID_PREFIX = APIPrefix.LETTER
    PYDANTIC_MODEL = PublicLetter

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[int | None] = mapped_column(nullable=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[str] = mapped_column()
    send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    letter_type: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column(nullable=True)

    participants: Mapped[list["User"]] = relationship(
        secondary=letter_to_user_assocation
    )
    group_id = Column(Integer, ForeignKey("group.id"))
    group: Mapped["Group"] = relationship(back_populates="letters")

    questions: Mapped[list["Question"]] = relationship(
        back_populates="letter", cascade="all"
    )

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple[UniqueConstraint | Index, ...]:
        """Define table constraints.

        Returns:
            tuple[UniqueConstraint | Index, ...]: Table constraints
        """
        return (
            UniqueConstraint(
                "group_id",
                "number",
                name="unique_group_letter_number",
            ),
            Index(
                "uniq_one_cyclic_upcoming_per_group",
                "group_id",
                unique=True,
                postgresql_where=text(
                    "letter_type = 'CYCLIC' AND status = 'UPCOMING'"
                ),
            ),
            Index(
                "uniq_one_cyclic_in_progress_per_group",
                "group_id",
                unique=True,
                postgresql_where=text(
                    "letter_type = 'CYCLIC' AND status = 'IN_PROGRESS'"
                ),
            ),
        )

    def __init__(
        self,
        group: Group,
        send_at: datetime,
        status: LetterStatus,
        number: int | None = None,
        letter_type: LetterType = LetterType.CYCLIC,
        title: str | None = None,
    ) -> None:
        """Initialize a new Letter instance.

        Args:
            group (Group): Group to which the letter belongs
            send_at (datetime): Scheduled send time of the letter
            status (LetterStatus): Initial status of the letter
            number (int | None, optional): Letter number. Defaults to None.
            letter_type (LetterType): Type of the letter
        """
        APIIdentified.__init__(self)
        if letter_type == LetterType.CYCLIC:
            self.number = (
                number
                if number is not None
                else next_cyclic_letter_number(group)
            )
        self.group = group
        self.participants = group.members
        self.send_at = send_at
        self.status = status
        self.letter_type = letter_type
        self.title = title

    @classmethod
    def create(
        cls,
        group: Group,
        send_at: datetime,
        letter_status: LetterStatus,
        number: int | None = None,
        letter_type: LetterType = LetterType.CYCLIC,
        title: str | None = None,
    ) -> Letter:
        """Create a new Letter instance.

        Factory method to create a new letter with the given parameters.

        Args:
            group (Group): Group to which the letter belongs
            send_at (datetime): Scheduled send time of the letter
            letter_status (LetterStatus): Initial status of the letter
            number (int | None, optional): Letter number. Defaults to None.
            letter_type (LetterType): Type of the letter

        Returns:
            Letter: New Letter instance
        """
        letter = cls(
            group,
            send_at,
            letter_status,
            number=number,
            letter_type=letter_type,
            title=title,
        )
        return letter

    @hybrid_property
    def responders(self) -> list[User]:
        """Get list of users who have responded to any question in the letter.

        Returns:
            list[User]: List of users who have submitted responses
        """
        respondents = {
            response.participant
            for question in self.questions
            for response in question.responses
        }
        return list(respondents)
