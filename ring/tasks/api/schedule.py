from __future__ import annotations
from fastapi import APIRouter, Depends
from ring.dependencies import (
    get_request_dependencies,
    AuthenticatedRequestDependencies,
)
from typing import TYPE_CHECKING
from ring.tasks.crud import (
    schedule as schedule_crud,
)
from ring.pydantic import ScheduleLinked as ScheduleSchema

if TYPE_CHECKING:
    from ring.postgres_models import Schedule

router = APIRouter()


@router.get(
    "/schedule/{group_api_id}",
    response_model=ScheduleSchema,
)
async def get_schedule_for_group(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Schedule:
    return schedule_crud.get_schedule_for_group(req_dep.db, group_api_id)
