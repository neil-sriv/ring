"""SQLAlchemy model for group invitations.

This module defines the Invite model for managing invitations to join groups,
including one-time tokens for secure registration and tracking of inviters.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import APIPrefix, register_api_class
from ring.created_at import CreatedAtMixin
from ring.parties.models.group_model import Group
from ring.parties.models.one_time_token_model import OneTimeToken
from ring.parties.models.user_model import User
from ring.parties.schemas.invite import InviteUnlinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

# Time-to-live for invite tokens in seconds (1 week)
DEFAULT_INVITE_TOKEN_TTL = 60 * 60 * 24 * 7


@register_api_class(APIPrefix.INVITE)
class Invite(Base, APIIdentified, PydanticModel, CreatedAtMixin):
    """SQLAlchemy model representing a group invitation.

    This model represents an invitation sent to a user's email address to join
    a group. Each invite has an associated one-time token for security and
    tracks the inviter and target group.

    Attributes:
        id (int): Primary key
        email (str): Email address of the invitee
        api_identifier (str): Unique API identifier with 'inv' prefix
        one_time_token_id (int): Foreign key to the associated token
        one_time_token (OneTimeToken): One-time use token for the invite
        inviter_id (int): Foreign key to the user sending the invite
        inviter (User): User who sent the invite
        group_id (int): Foreign key to the target group
        group (Group): Group the invitee is being invited to
        created_at (datetime): Timestamp of invite creation
    """

    __tablename__ = "invite"

    API_ID_PREFIX = APIPrefix.INVITE
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
        """Initialize a new invite.

        Args:
            email (str): Email address of the invitee
            token (OneTimeToken): One-time token for the invite
            inviter (User): User sending the invite
            group (Group): Group to invite the user to
        """
        APIIdentified.__init__(self)
        self.email = email
        self.one_time_token = token
        self.inviter = inviter
        self.group = group

    @classmethod
    def create(
        cls, email: str, token: OneTimeToken, inviter: User, group: Group
    ) -> Invite:
        """Create a new invite instance.

        Args:
            email (str): Email address of the invitee
            token (OneTimeToken): One-time token for the invite
            inviter (User): User sending the invite
            group (Group): Group to invite the user to

        Returns:
            Invite: New invite instance
        """
        return cls(email, token, inviter, group)
