"""SQLAlchemy models for one-time use tokens.

This module defines models for managing one-time use tokens used in features
like group invitations and password resets, with built-in expiration tracking.
"""

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
        INVITE (str): Token used for group invitations
        PASSWORD_RESET (str): Token used for password reset requests
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

        Args:
            token (str): The token string
            type (TokenType): Type of token (invite or password reset)
            email (str | None, optional): Associated email address. Defaults to None.
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

        Args:
            token (str): The token string
            type (TokenType): Type of token (invite or password reset)
            email (str | None, optional): Associated email address. Defaults to None.

        Returns:
            OneTimeToken: New token instance
        """
        return cls(token, type, email)

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if the token has expired.

        Returns:
            bool: True if the token has expired, False otherwise
        """
        return self.created_at + timedelta(seconds=self.ttl) < datetime.now(
            UTC
        )

    @is_expired.expression
    def is_expired(cls) -> ColumnElement[bool]:
        """SQLAlchemy expression for checking token expiration.

        Returns:
            ColumnElement[bool]: SQL expression for token expiration check
        """
        return func.trunc(
            extract("epoch", cls.created_at)
        ) + cls.ttl < func.trunc(extract("epoch", func.now()))
