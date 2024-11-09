from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.ring_pydantic.linked_schemas import ScheduleLinked
from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base
from ring.tasks.models.task_model import Task, TaskStatus, TaskType

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

    @hybrid_property
    def send_email_tasks(self) -> list[Task]:
        return [
            task
            for task in self.tasks
            if task.type == TaskType.SEND_EMAIL
            and task.status == TaskStatus.PENDING
        ]

    @hybrid_property
    def reminder_email_tasks(self) -> list[Task]:
        return [
            task
            for task in self.tasks
            if task.type == TaskType.REMINDER_EMAIL
            and task.status == TaskStatus.PENDING
        ]
