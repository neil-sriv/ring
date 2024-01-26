from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    pass


class TaskCreate(TaskBase):
    schedule_api_identifier: str


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    type: str
    status: str
    execute_at: datetime


class TaskUnlinked(Task):
    pass
