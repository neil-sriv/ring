from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING
from ring.crud import (
    schedule as schedule_crud,
)
from ring.pydantic_schemas import ScheduleLinked as ScheduleSchema
from ring.pydantic_schemas.schedule import ScheduleCreate
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models import Schedule


@internal.post(
    "/schedule/{group_api_id}",
    response_model=ScheduleSchema,
)
def add_schedule_to_group(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
) -> Schedule:
    return schedule_crud.create_schedule_for_group(db, schedule)
