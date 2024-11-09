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

DEFAULT_TOKEN_TTL = 60 * 60 * 24 * 7  # 1 week


class TokenType(StrEnum):
    INVITE = "invite"
    PASSWORD_RESET = "password_reset"


class OneTimeToken(Base, CreatedAtMixin):
    __tablename__ = "one_time_token"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column()
    ttl: Mapped[float] = mapped_column()
    used: Mapped[bool] = mapped_column(
        server_default=sqlalchemy.false(), nullable=False
    )
    type: Mapped[str] = mapped_column(nullable=False)

    def __init__(
        self,
        token: str,
        type: TokenType,
    ) -> None:
        self.token = token
        self.type = type
        self.ttl = DEFAULT_TOKEN_TTL
        self.used = False

    @classmethod
    def create(cls, token: str, type: TokenType) -> OneTimeToken:
        return cls(token, type)

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
