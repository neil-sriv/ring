from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from ring.pydantic_schemas.group import GroupUnlinked


class ScheduleBase(BaseModel):
    pass


class ScheduleCreate(ScheduleBase):
    group: "GroupUnlinked"


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class ScheduleLinked(Schedule):
    group: "GroupUnlinked"


class ScheduleUnlinked(Schedule):
    pass
