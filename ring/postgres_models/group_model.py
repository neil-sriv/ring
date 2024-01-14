from __future__ import annotations
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ring.sqlalchemy_base import Base
from ring.postgres_models.user_group_assocation import user_group_association


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    members: Mapped[list["User"]] = relationship(
        secondary=user_group_association, back_populates="groups"
    )
    letters: Mapped[list["Letter"]] = relationship(back_populates="group")
