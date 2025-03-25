"""SQLAlchemy models for Ring's task system.

This module defines the database models for Ring's asynchronous task system, including
the base Task model and its specialized variants. It uses SQLAlchemy's declarative
base and polymorphic inheritance to support different types of tasks.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.tasks.models.schedule_model import Schedule


class TaskStatus(StrEnum):
    """Enumeration of possible task statuses.
    
    Attributes:
        PENDING: Task is waiting to be executed
        IN_PROGRESS: Task is currently being executed
        COMPLETED: Task has finished successfully
        FAILED: Task execution failed
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(StrEnum):
    """Enumeration of supported task types.
    
    Attributes:
        GENERIC: Base task type for general purposes
        SEND_EMAIL: Task for sending emails
        REMINDER_EMAIL: Task for sending reminder emails
    """
    GENERIC = "generic"
    SEND_EMAIL = "send_email"
    REMINDER_EMAIL = "reminder_email"


class Task(Base):
    """Base model for all asynchronous tasks in Ring.
    
    This model uses SQLAlchemy's polymorphic inheritance to support different types
    of tasks while maintaining a common interface. Each task is associated with a
    schedule and contains execution details like timing and status.

    Attributes:
        id: Unique identifier for the task
        schedule_id: Foreign key to the associated schedule
        schedule: Relationship to the Schedule model
        type: Type of task (used for polymorphic identity)
        status: Current status of the task
        execute_at: When the task should be executed
        arguments: JSON-encoded arguments for task execution
        message: Optional message or error details
    """
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedule.id"),
        index=True,
    )
    schedule: Mapped["Schedule"] = relationship(back_populates="tasks")
    type: Mapped[str] = mapped_column(index=True, nullable=False)
    status: Mapped[str] = mapped_column(index=True, nullable=False)
    execute_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    arguments: Mapped[dict[str, str]] = mapped_column(type_=JSON)
    message: Mapped[str] = mapped_column(nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": TaskType.GENERIC,
    }

    def __init__(
        self,
        schedule: Schedule,
        execute_at: datetime,
        task_type: TaskType = TaskType.GENERIC,
        arguments: dict[str, str] = {},
    ) -> None:
        """Initialize a new Task.

        Args:
            schedule: The Schedule this task belongs to
            execute_at: When the task should be executed
            task_type: Type of task (defaults to GENERIC)
            arguments: Optional arguments for task execution
        """
        self.schedule = schedule
        self.type = task_type
        self.status = TaskStatus.PENDING
        self.execute_at = execute_at
        self.arguments = arguments

    @classmethod
    def create(
        cls,
        schedule: Schedule,
        task_type: TaskType,
        execute_at: datetime,
        arguments: dict[str, str],
    ) -> Task:
        """Factory method to create a new Task.

        Args:
            schedule: The Schedule this task belongs to
            task_type: Type of task
            execute_at: When the task should be executed
            arguments: Arguments for task execution

        Returns:
            Task: A new Task instance
        """
        return cls(
            schedule=schedule,
            task_type=task_type,
            execute_at=execute_at,
            arguments=arguments,
        )

    def __repr__(self) -> str:
        """Return a JSON string representation of the task."""
        return json.dumps(self.__dict__, indent=4, default=str)


class ReminderEmailTask(Task):
    """Task model for sending reminder emails.
    
    This specialized task type handles the sending of reminder emails to users.
    It inherits all attributes from the base Task model.
    """
    __mapper_args__ = {
        "polymorphic_identity": TaskType.REMINDER_EMAIL,
    }


class SendEmailTask(Task):
    """Task model for sending regular emails.
    
    This specialized task type handles the sending of regular emails.
    It inherits all attributes from the base Task model.
    """
    __mapper_args__ = {
        "polymorphic_identity": TaskType.SEND_EMAIL,
    }

    # @classmethod
    # def create(
    #     cls,
    #     schedule: Schedule,
    #     letter_api_id: str,
    #     send_at: datetime,
    #     **kwargs: Any,
    # ) -> SendEmailTask:
    #     return cls(
    #         schedule=schedule,
    #         task_type=TaskType.SEND_EMAIL,
    #         arguments={
    #             "letter_api_id": letter_api_id,
    #             "send_at": send_at.isoformat(),
    #         },
    #     )
