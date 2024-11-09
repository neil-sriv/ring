from __future__ import annotations
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey
from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
from ring.parties.models.group_model import Group
from ring.parties.models.one_time_token_model import OneTimeToken
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
    email: Mapped[str] = mapped_column(index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    one_time_token_id: Mapped[int] = mapped_column(
        ForeignKey(
            "one_time_token.id",
            name="invite_one_time_token_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        unique=True,
    )

    one_time_token: Mapped["OneTimeToken"] = relationship(
        "OneTimeToken", uselist=False
    )

    inviter_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user.id", name="invite_inviter_id_fkey", ondelete="CASCADE"
        )
    )
    inviter: Mapped[User] = relationship()

    group_id: Mapped[int] = mapped_column(
        ForeignKey("group.id", name="invite_group_id_fkey", ondelete="CASCADE")
    )
    group: Mapped[Group] = relationship()

    def __init__(
        self,
        email: str,
        token: OneTimeToken,
        inviter: User,
        group: Group,
    ) -> None:
        APIIdentified.__init__(self)
        self.email = email
        self.one_time_token = token
        self.inviter = inviter
        self.group = group

    @classmethod
    def create(
        cls, email: str, token: OneTimeToken, inviter: User, group: Group
    ) -> Invite:
        return cls(email, token, inviter, group)
