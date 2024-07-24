from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ring.api_identifier.api_identified_model import APIIdentified

from ring.pydantic.pydantic_model import PydanticModel
from ring.pydantic.linked_schemas import UserLinked
from ring.sqlalchemy_base import Base
from ring.parties.models.user_group_assocation import user_group_association

if TYPE_CHECKING:
    from ring.parties.models.group_model import Group
    from ring.letters.models.response_model import Response


class User(Base, APIIdentified, PydanticModel):
    __tablename__ = "user"

    API_ID_PREFIX = "usr"
    PYDANTIC_MODEL = UserLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    groups: Mapped[list["Group"]] = relationship(
        secondary=user_group_association, back_populates="members"
    )
    responses: Mapped[list["Response"]] = relationship(
        back_populates="participant",
    )

    def __init__(
        self,
        email: str,
        name: Optional[str],
        hashed_password: str,
    ) -> None:
        APIIdentified.__init__(self)
        self.email = email
        self.name = name
        self.hashed_password = hashed_password

    @classmethod
    def create(
        cls,
        email: str,
        name: Optional[str],
        hashed_password: str,
    ) -> User:
        return cls(email, name, hashed_password)
