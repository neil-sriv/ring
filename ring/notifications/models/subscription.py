from __future__ import annotations

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import SubscriptionLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


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

    user_id: Mapped[int] = mapped_column(index=True, nullable=False)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notification_subscriptions",
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
