"""SQLAlchemy model for Ring's task scheduling system.

This module defines the Schedule model which manages task scheduling for groups.
Each group can have one schedule that contains multiple tasks of different types.
The Schedule model provides methods to access and manage these tasks efficiently.
"""

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
    """Schedule model for managing group tasks.

    This model represents a schedule associated with a group, managing various types
    of tasks like email sending and reminders. Each group can have only one schedule,
    enforced by a unique constraint on group_id.

    Attributes:
        id: Unique identifier for the schedule
        group_id: Foreign key to the associated group
        group: Relationship to the Group model
        tasks: List of tasks associated with this schedule
    """

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
        """Create a new schedule for a group.

        Args:
            group: The group to create a schedule for

        Returns:
            Schedule: A new Schedule instance

        Raises:
            ValueError: If the group already has a schedule
        """
        if group.schedule:
            raise ValueError("Group already has a schedule")
        return cls(group=group)

    @hybrid_property
    def send_email_tasks(self) -> list[Task]:
        """Get all pending email send tasks.

        Returns:
            list[Task]: List of pending tasks of type SEND_EMAIL
        """
        return [
            task
            for task in self.tasks
            if task.type == TaskType.SEND_EMAIL
            and task.status == TaskStatus.PENDING
        ]

    @hybrid_property
    def reminder_email_tasks(self) -> list[Task]:
        """Get all pending reminder email tasks.

        Returns:
            list[Task]: List of pending tasks of type REMINDER_EMAIL
        """
        return [
            task
            for task in self.tasks
            if task.type == TaskType.REMINDER_EMAIL
            and task.status == TaskStatus.PENDING
        ]
