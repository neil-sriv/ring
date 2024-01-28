from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from ring.pydantic_schemas.task import TaskUnlinked


class ScheduleBase(BaseModel):
    pass


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)


class ScheduleUnlinked(Schedule):
    tasks: list["TaskUnlinked"]


class ScheduleSendParam(BaseModel):
    letter_api_id: str
    send_at: datetime
