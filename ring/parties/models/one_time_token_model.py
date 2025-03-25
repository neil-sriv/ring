from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

import sqlalchemy
from sqlalchemy import ColumnElement, extract, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from ring.created_at import CreatedAtMixin

# from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base

# Time-to-live for tokens in seconds (1 week)
DEFAULT_TOKEN_TTL = 60 * 60 * 24 * 7


class TokenType(StrEnum):
    """Enumeration of possible one-time token types.

    Attributes:
        INVITE: Token used for group invitations
        PASSWORD_RESET: Token used for password reset requests
    """

    INVITE = "invite"
    PASSWORD_RESET = "password_reset"


class OneTimeToken(Base, CreatedAtMixin):
    """SQLAlchemy model representing a one-time use token.

    This model represents tokens that can only be used once for specific purposes
    like invites or password resets. Each token has a time-to-live (TTL) and
    tracks whether it has been used.

    Attributes:
        id (int): Primary key
        token (str): The actual token string
        ttl (float): Time-to-live in seconds
        used (bool): Whether the token has been used
        type (str): Type of token (invite or password reset)
        email (str): Associated email address (optional)
        created_at (datetime): Timestamp of token creation
    """

    __tablename__ = "one_time_token"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column()
    ttl: Mapped[float] = mapped_column()
    used: Mapped[bool] = mapped_column(
        server_default=sqlalchemy.false(), nullable=False
    )
    type: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(index=True, nullable=True)

    def __init__(
        self,
        token: str,
        type: TokenType,
        email: str | None = None,
    ) -> None:
        """Initialize a new one-time token.

        :param token: The token string
        :type token: str
        :param type: Type of token (invite or password reset)
        :type type: TokenType
        :param email: Associated email address, defaults to None
        :type email: str | None
        """
        self.token = token
        self.type = type
        self.ttl = DEFAULT_TOKEN_TTL
        self.used = False
        if email:
            self.email = email

    @classmethod
    def create(
        cls,
        token: str,
        type: TokenType,
        email: str | None = None,
    ) -> OneTimeToken:
        """Create a new one-time token instance.

        :param token: The token string
        :type token: str
        :param type: Type of token (invite or password reset)
        :type type: TokenType
        :param email: Associated email address, defaults to None
        :type email: str | None
        :return: New token instance
        :rtype: OneTimeToken
        """
        return cls(token, type, email)

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if the token has expired.

        :return: True if the token has expired, False otherwise
        :rtype: bool
        """
        return self.created_at + timedelta(seconds=self.ttl) < datetime.now(
            UTC
        )

    @is_expired.expression
    def is_expired(cls) -> ColumnElement[bool]:
        """SQLAlchemy expression for checking token expiration.

        :return: SQL expression for token expiration check
        :rtype: ColumnElement[bool]
        """
        return func.trunc(
            extract("epoch", cls.created_at)
        ) + cls.ttl < func.trunc(extract("epoch", func.now()))
