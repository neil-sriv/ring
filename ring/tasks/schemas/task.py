"""Pydantic schemas for task-related API operations.

This module defines the Pydantic models used for validating and serializing task data
in API requests and responses. It includes models for creating tasks and representing
task data with different levels of detail.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class TaskBase(BaseModel):
    """Base schema for task-related operations.

    This is the base class for all task schemas, providing common fields
    and validation rules.
    """

    pass


class TaskCreate(TaskBase):
    """Schema for creating a new task.

    Attributes:
        schedule_api_identifier: API identifier of the schedule to create the task for
    """

    schedule_api_identifier: str


class Task(TaskBase):
    """Schema for task data in API responses.

    Attributes:
        type: Type of the task (e.g., "send_email", "reminder_email")
        status: Current status of the task
        execute_at: When the task should be executed
        arguments: Task-specific arguments as key-value pairs
    """

    model_config = ConfigDict(from_attributes=True)

    type: str
    status: str
    execute_at: AwareDatetime
    arguments: dict[str, str]


class TaskUnlinked(Task):
    """Schema for task data without linked relationships.

    This schema extends the base Task schema but excludes any linked relationships,
    useful for nested serialization to avoid circular references.
    """

    pass
