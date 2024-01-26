from __future__ import annotations
from enum import StrEnum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.group_model import Group


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskType(StrEnum):
    GENERIC = "generic"
    SEND_EMAIL = "send_email"


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedule.id"),
        index=True,
    )
    schedule: Mapped["Schedule"] = relationship(back_populates="tasks")
    type: Mapped[str] = mapped_column(index=True, nullable=False)
    status: Mapped[str] = mapped_column(index=True, nullable=False)
    execute_at: Mapped[datetime] = mapped_column(index=True)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": TaskType.GENERIC,
    }

    @classmethod
    def create(cls, schedule: Schedule) -> Task:
        return cls(schedule=schedule)


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("group.id"),
        nullable=False,
    )
    group: Mapped["Group"] = relationship(back_populates="schedule")
    tasks: Mapped[list["Task"]] = relationship(back_populates="schedule")

    __table_args__ = (UniqueConstraint("group_id", name="unique_group_schedule"),)

    @classmethod
    def create(cls, group: Group) -> Schedule:
        if group.schedule:
            raise ValueError("Group already has a schedule")
        return cls(group=group)
