from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.ring_pydantic import ScheduleLinked as ScheduleSchema
from ring.tasks.crud import (
    schedule as schedule_crud,
)

if TYPE_CHECKING:
    from ring.tasks.models.schedule_model import Schedule

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
