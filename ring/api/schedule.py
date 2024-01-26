from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING
from ring.crud import (
    schedule as schedule_crud,
)
from ring.pydantic_schemas import ScheduleLinked as ScheduleSchema
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models import Schedule


@internal.get(
    "/schedule/{group_api_id}",
    response_model=ScheduleSchema,
)
def get_schedule_for_group(
    group_api_id: str,
    db: Session = Depends(get_db),
) -> Schedule:
    return schedule_crud.get_schedule_for_group(db, group_api_id)
