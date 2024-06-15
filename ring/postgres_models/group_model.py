from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from ring.postgres_models.api_identified import APIIdentified

from ring.postgres_models.pydantic_model import PydanticModel
from ring.pydantic_schemas.linked_schemas import GroupLinked
from ring.sqlalchemy_base import Base
from ring.postgres_models.user_group_assocation import user_group_association
from ring.postgres_models.schedule_model import Schedule


if TYPE_CHECKING:
    from ring.postgres_models.letter_model import Letter
    from ring.postgres_models.user_model import User


class Group(Base, PydanticModel, APIIdentified):
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
