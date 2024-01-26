from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class ScheduleBase(BaseModel):
    pass


class ScheduleCreate(ScheduleBase):
    group_api_identifier: str


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)


class ScheduleUnlinked(Schedule):
    pass
