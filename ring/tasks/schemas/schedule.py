"""Pydantic schemas for schedule-related API operations.

This module defines the Pydantic models used for validating and serializing schedule data
in API requests and responses. It includes models for managing schedules and their
associated tasks, as well as parameters for scheduling operations.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.tasks.schemas.task import TaskUnlinked


class ScheduleBase(BaseModel):
    """Base schema for schedule-related operations.

    This is the base class for all schedule schemas, providing common fields
    and validation rules.
    """

    pass


class Schedule(ScheduleBase):
    """Schema for schedule data in API responses.

    This schema represents a schedule with its basic attributes, configured to work
    with SQLAlchemy models.
    """

    model_config = ConfigDict(from_attributes=True)


class ScheduleUnlinked(Schedule):
    """Schema for schedule data with unlinked task relationships.

    This schema extends the base Schedule schema and includes a list of tasks,
    using the unlinked task schema to avoid circular references.

    Attributes:
        tasks: List of tasks associated with this schedule
    """

    tasks: list["TaskUnlinked"]


class ScheduleSendParam(BaseModel):
    """Parameters for scheduling a send operation.

    This schema defines the parameters needed to schedule a send operation
    for a letter.

    Attributes:
        letter_api_id: API identifier of the letter to send
        send_at: When the letter should be sent
    """

    letter_api_id: str
    send_at: AwareDatetime
