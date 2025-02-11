from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.tasks.schemas.task import TaskUnlinked


class ScheduleBase(BaseModel):
    pass


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)


class ScheduleUnlinked(Schedule):
    tasks: list["TaskUnlinked"]


class ScheduleSendParam(BaseModel):
    letter_api_id: str
    send_at: AwareDatetime
