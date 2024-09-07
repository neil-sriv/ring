from __future__ import annotations
from datetime import UTC, datetime, timedelta
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ColumnElement, extract, func, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.parties.schemas.invite import InviteUnlinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base
from ring.parties.models.user_model import User


DEFAULT_INVITE_TOKEN_TTL = 60 * 60 * 24 * 7  # 1 week


class Invite(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    __tablename__ = "invite"

    API_ID_PREFIX = "inv"
    PYDANTIC_MODEL = InviteUnlinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    token: Mapped[str] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)
    ttl: Mapped[float] = mapped_column()

    inviter_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    inviter: Mapped[User] = relationship(
        back_populates="invites", cascade="all"
    )

    def __init__(
        self,
        email: str,
        token: str,
        inviter: User,
    ) -> None:
        APIIdentified.__init__(self)
        self.email = email
        self.token = token
        self.inviter = inviter
        self.ttl = DEFAULT_INVITE_TOKEN_TTL

    @classmethod
    def create(
        cls,
        email: str,
        token: str,
        inviter: User,
    ) -> Invite:
        return cls(email, token, inviter)

    @hybrid_property
    def is_expired(self) -> bool:
        return self.created_at + timedelta(seconds=self.ttl) < datetime.now(
            UTC
        )

    @is_expired.expression
    def is_expired(cls) -> ColumnElement[bool]:
        return func.trunc(
            extract("epoch", cls.created_at)
        ) + cls.ttl < func.trunc(extract("epoch", func.now()))
