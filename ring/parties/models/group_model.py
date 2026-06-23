"""SQLAlchemy model for group management.

This module defines the Group model for managing user groups in the Ring system,
including membership, letters, and scheduling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.letters.constants import LetterStatus, LetterType
from ring.letters.models.default_question_model import DefaultQuestion
from ring.letters.models.letter_model import Letter
from ring.letters.send_threshold import get_group_min_responder_ratio
from ring.parties.models.group_key_value import GroupKeyValue
from ring.parties.models.user_group_assocation import user_group_association
from ring.ring_pydantic.linked_schemas import GroupLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base
from ring.tasks.models.schedule_model import Schedule

if TYPE_CHECKING:
    from ring.parties.models.user_model import User


@register_api_class(APIPrefix.GROUP)
class Group(Base, PydanticModel, APIIdentified, CreatedAtMixin):
    """SQLAlchemy model representing a group of users.

    This model represents a group that users can join, with an admin user,
    scheduled letters, default questions, and associated metadata.

    Attributes:
        id (int): Primary key
        name (str): Unique group name
        api_identifier (str): Unique API identifier with 'grp' prefix
        cycle_length (int): Number of days between letters, defaults to 30
        admin_id (int): Foreign key to the admin user
        admin (User): Admin user relationship
        members (list[User]): Group members
        letters (list[Letter]): Letters associated with the group
        schedule (Schedule): Group's task schedule
        default_questions (list[DefaultQuestion]): Default questions for letters
        key_values (GroupKeyValue): Additional group metadata
        created_at (datetime): Timestamp of group creation
    """

    __tablename__ = "group"

    API_ID_PREFIX = APIPrefix.GROUP
    PYDANTIC_MODEL = GroupLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    cycle_length: Mapped[int] = mapped_column(default=30)

    admin_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    _admin = relationship("User", foreign_keys=[admin_id])
    members: Mapped[list["User"]] = relationship(
        secondary=user_group_association, back_populates="groups"
    )
    letters: Mapped[list["Letter"]] = relationship(
        back_populates="group", cascade="all"
    )
    schedule: Mapped["Schedule"] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    default_questions: Mapped[list["DefaultQuestion"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    key_values: Mapped["GroupKeyValue"] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    def __init__(self, name: str, admin: User) -> None:
        """Initialize a new group.

        Args:
            name (str): Group name
            admin (User): User who will be the group admin
        """
        APIIdentified.__init__(self)
        self.schedule = Schedule.create(self)
        self.name = name
        self.members = [admin]
        self.admin = admin
        self.key_values = GroupKeyValue.create(self)

    @classmethod
    def create(cls, name: str, admin: User) -> Group:
        """Create a new group instance.

        Args:
            name (str): Group name
            admin (User): User who will be the group admin

        Returns:
            Group: New group instance
        """
        return cls(name, admin)

    @hybrid_property
    def admin(self) -> User:  # type: ignore
        """Get the group's admin user.

        Returns:
            User: Admin user
        """
        return self._admin

    @admin.setter  # type: ignore
    def admin(self, admin: User) -> None:
        """Set the group's admin user.

        Args:
            admin (User): New admin user

        Raises:
            ValueError: If admin is not a member of the group
        """
        if admin in self.members:
            self._admin = admin
        else:
            raise ValueError("Admin must be a member of the group")

    @hybrid_property
    def min_responder_ratio(self) -> float | None:
        """Configured minimum responder ratio before send, or None for default."""
        return get_group_min_responder_ratio(self)

    @hybrid_property
    def cyclic_letters(self) -> list[Letter]:
        """Get the group's cyclic letters.

        Returns:
            list[Letter]: Cyclic letters
        """
        return [
            letter
            for letter in self.letters
            if letter.letter_type == LetterType.CYCLIC
        ]

    @hybrid_property
    def upcoming_letters(self) -> list[Letter]:
        """Get the group's upcoming letters.

        Returns:
            list[Letter]: Upcoming letters
        """
        return sorted(
            [
                letter
                for letter in self.cyclic_letters
                if letter.status == LetterStatus.UPCOMING
            ],
            key=lambda x: x.send_at,
        )

    @hybrid_property
    def in_progress_letters(self) -> list[Letter]:
        """Get the group's in-progress letters.

        Returns:
            list[Letter]: In-progress letters
        """
        return sorted(
            [
                letter
                for letter in self.cyclic_letters
                if letter.status == LetterStatus.IN_PROGRESS
            ],
            key=lambda x: x.send_at,
        )
