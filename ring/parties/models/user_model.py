from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.letters.models.response_model import Response
from ring.parties.models.user_group_assocation import user_group_association
from ring.ring_pydantic.linked_schemas import UserLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    # from ring.notifications.models.subscription import Subscription
    from ring.parties.models.group_model import Group


class User(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    __allow_unmapped__ = True
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
    # notification_subscriptions: Mapped[list["Subscription"]] = relationship(
    #     "Subscription",
    #     cascade="all, delete-orphan",
    #     back_populates="user",
    #     foreign_keys="[Subscription.user_id]",
    # )

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
