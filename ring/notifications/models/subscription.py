from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.ring_pydantic.linked_schemas import SubscriptionLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.user_model import User


class Subscription(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    __tablename__ = "subscription"

    API_ID_PREFIX = "sbscrp"
    PYDANTIC_MODEL = SubscriptionLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    endpoint: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )
    keys: Mapped[dict[str, str | float | bool]] = mapped_column(
        JSONB,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id", name="subscription_user_id_fkey", ondelete="CASCADE"
        ),
        index=True,
        nullable=False,
    )
    user: Mapped["User"] = relationship(
        "User",
        # back_populates="notification_subscriptions",
        foreign_keys=[user_id],
    )

    def __init__(
        self,
        endpoint: str,
        keys: dict[str, str | float | bool],
        user: User,
    ) -> None:
        APIIdentified.__init__(self)
        self.endpoint = endpoint
        self.keys = keys
        self.user = user

    @classmethod
    def create(
        cls,
        endpoint: str,
        keys: dict[str, str | float | bool],
        user: User,
    ) -> Subscription:
        return cls(endpoint, keys, user)
