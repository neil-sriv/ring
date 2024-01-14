from __future__ import annotations
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String

from ring.fast import Base
from ring.postgres_models.user_group_assocation import user_group_association


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[String] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[String] = mapped_column()
    api_identifier: Mapped[String] = mapped_column(unique=True, index=True)

    groups: Mapped[list["Group"]] = relationship(
        secondary=user_group_association, back_populates="members"
    )
