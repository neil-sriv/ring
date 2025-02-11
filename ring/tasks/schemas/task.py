from pydantic import AwareDatetime, BaseModel, ConfigDict


class TaskBase(BaseModel):
    pass


class TaskCreate(TaskBase):
    schedule_api_identifier: str


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    type: str
    status: str
    execute_at: AwareDatetime
    arguments: dict[str, str]


class TaskUnlinked(Task):
    pass
