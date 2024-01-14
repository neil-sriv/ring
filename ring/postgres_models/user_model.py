from __future__ import annotations
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.sqlalchemy_base import Base
from ring.postgres_models.user_group_assocation import user_group_association


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    groups: Mapped[list["Group"]] = relationship(
        secondary=user_group_association, back_populates="members"
    )
    responses: Mapped[list["Response"]] = relationship(back_populates="participant")
