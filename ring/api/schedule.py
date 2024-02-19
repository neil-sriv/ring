from __future__ import annotations
from fastapi import Depends
from ring.dependencies import (
    get_request_dependencies,
    AuthenticatedRequestDependencies,
)
from typing import TYPE_CHECKING
from ring.crud import (
    schedule as schedule_crud,
)
from ring.pydantic_schemas import ScheduleLinked as ScheduleSchema
from ring.routes import internal

if TYPE_CHECKING:
    from ring.postgres_models import Schedule


@internal.get(
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
