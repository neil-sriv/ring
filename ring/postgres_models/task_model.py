from __future__ import annotations
from enum import StrEnum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ring.sqlalchemy_base import Base

if TYPE_CHECKING:
    from ring.postgres_models.schedule_model import Schedule


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
    execute_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    arguments: Mapped[dict[str, str]] = mapped_column(type_=JSON)

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
        return cls(
            schedule=schedule,
            task_type=task_type,
            execute_at=execute_at,
            arguments=arguments,
        )


class SendEmailTask(Task):
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
