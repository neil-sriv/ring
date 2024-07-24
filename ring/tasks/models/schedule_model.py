from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ring.pydantic.pydantic_model import PydanticModel
from ring.tasks.models.task_model import Task

from ring.pydantic.linked_schemas import ScheduleLinked
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.parties.models.group_model import Group


class Schedule(Base, PydanticModel):
    __tablename__ = "schedule"

    PYDANTIC_MODEL = ScheduleLinked

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("group.id"),
        nullable=False,
    )
    group: Mapped["Group"] = relationship(back_populates="schedule")
    tasks: Mapped[list["Task"]] = relationship(back_populates="schedule")

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            name="unique_group_schedule",
        ),
    )

    @classmethod
    def create(cls, group: Group) -> Schedule:
        if group.schedule:
            raise ValueError("Group already has a schedule")
        return cls(group=group)
