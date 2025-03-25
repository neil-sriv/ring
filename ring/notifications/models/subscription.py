from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import SubscriptionLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


class Subscription(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model for web push notification subscriptions.

    This model represents a web push notification subscription for a user,
    storing the endpoint URL and associated keys required for sending
    push notifications through the Web Push protocol.

    Attributes:
        id (int): Primary key
        endpoint (str): Push notification endpoint URL
        keys (dict): Dictionary containing encryption keys and auth info
        user_id (int): Foreign key to the associated user
        user (User): Relationship to the user model
        api_identifier (str): Unique API identifier with 'sbscrp' prefix
        created_at (datetime): Timestamp of subscription creation
    """

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
        """Initialize a new subscription.

        :param endpoint: Push notification endpoint URL
        :type endpoint: str
        :param keys: Dictionary containing encryption keys and auth info
        :type keys: dict[str, str | float | bool]
        :param user: User to associate the subscription with
        :type user: User
        """
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
        """Create a new subscription instance.

        :param endpoint: Push notification endpoint URL
        :type endpoint: str
        :param keys: Dictionary containing encryption keys and auth info
        :type keys: dict[str, str | float | bool]
        :param user: User to associate the subscription with
        :type user: User
        :return: New subscription instance
        :rtype: Subscription
        """
        return cls(endpoint, keys, user)


User.notification_subscriptions = relationship(
    "Subscription", back_populates="user", cascade="all, delete-orphan"
)
