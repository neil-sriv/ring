
from __future__ import annotations
from datetime import UTC, datetime, timedelta
import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ColumnElement, extract, func
from sqlalchemy.ext.hybrid import hybrid_property
from ring.api_identifier.api_identified_model import APIIdentified
from ring.created_at import CreatedAtMixin
# from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


DEFAULT_TOKEN_TTL = 60 * 60 * 24 * 7  # 1 week


class OneTimeToken(Base, CreatedAtMixin):
    __tablename__ = "one_time_token"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column()
    ttl: Mapped[float] = mapped_column()
    used: Mapped[bool] = mapped_column(
        server_default=sqlalchemy.false(), nullable=False
    )

    def __init__(
        self,
        token: str,
    ) -> None:
        self.token = token
        self.ttl = DEFAULT_TOKEN_TTL
        self.used = False

    @classmethod
    def create(
        cls, token: str
    ) -> OneTimeToken:
        return cls(token)

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
