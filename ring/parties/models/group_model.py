from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.parties.models.user_group_assocation import user_group_association
from ring.ring_pydantic.linked_schemas import GroupLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base
from ring.tasks.models.schedule_model import Schedule

if TYPE_CHECKING:
    from ring.parties.models.user_model import User
    from ring.letters.models.default_question import DefaultQuestion


class Group(Base, PydanticModel, APIIdentified, CreatedAtMixin):
    __tablename__ = "group"

    API_ID_PREFIX = "grp"
    PYDANTIC_MODEL = GroupLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

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

    def __init__(self, name: str, admin: User) -> None:
        APIIdentified.__init__(self)
        self.schedule = Schedule.create(self)
        self.name = name
        self.members = [admin]
        self.admin = admin

    @classmethod
    def create(cls, name: str, admin: User) -> Group:
        return cls(name, admin)

    @hybrid_property
    def admin(self) -> User:  # type: ignore
        return self._admin

    @admin.setter  # type: ignore
    def admin(self, admin: User) -> None:
        if admin in self.members:
            self._admin = admin
        else:
            raise ValueError("Admin must be a member of the group")

    @hybrid_property
    def in_progress_letter(self) -> Letter | None:
        upcoming = [
            letter
            for letter in self.letters
            if letter.status == LetterStatus.IN_PROGRESS
        ]
        assert len(upcoming) <= 1
        return upcoming[0] if upcoming else None

    @hybrid_property
    def upcoming_letter(self) -> Letter | None:
        upcoming = [
            letter
            for letter in self.letters
            if letter.status == LetterStatus.UPCOMING
        ]
        assert len(upcoming) <= 1
        return upcoming[0] if upcoming else None
