"""In-app inbox item model.

Web push sends are not stored on their own. An inbox row is the persisted
copy of a send so the app can list it, track unread state, and link to the
letter or group the send was about.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.notifications.crud.links import inbox_href
from ring.notifications.schemas.inbox import InboxItemResponse
from ring.parties.models.user_model import User
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


@register_api_class(APIPrefix.INBOX)
class InboxItem(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """A single in-app notification for one recipient.

    ``target_api_id`` is a weak reference to the letter or group the send
    pointed at. The SPA path is derived from that id so group links stay on
    ``/groups/{id}/loops``.
    """

    __tablename__ = "inbox_item"

    API_ID_PREFIX = APIPrefix.INBOX
    PYDANTIC_MODEL = InboxItemResponse

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False)
    target_api_id: Mapped[str | None] = mapped_column(nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id",
            name="inbox_item_user_id_fkey",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="inbox_items",
    )

    def __init__(
        self,
        user: User,
        title: str,
        body: str,
        target_api_id: str | None,
    ) -> None:
        APIIdentified.__init__(self)
        self.user = user
        self.title = title
        self.body = body
        self.target_api_id = target_api_id
        self.read_at = None

    @classmethod
    def create(
        cls,
        user: User,
        title: str,
        body: str,
        target_api_id: str | None,
    ) -> InboxItem:
        return cls(user, title, body, target_api_id)

    @property
    def href(self) -> str:
        return inbox_href(self.target_api_id)

    @property
    def unread(self) -> bool:
        return self.read_at is None


User.inbox_items = relationship(
    "InboxItem",
    back_populates="user",
    cascade="all, delete-orphan",
)
