"""API endpoints for managing task schedules.

This module provides FastAPI route handlers for retrieving and managing schedules
associated with groups. It includes endpoints for viewing task schedules and their
associated tasks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from ring.fastapp.dependencies import (
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
    """Get a group's schedule by its API identifier.

    Args:
        group_api_id: API identifier of the group
        req_dep: Request dependencies including database session

    Returns:
        Schedule: The group's schedule with its associated tasks

    Raises:
        HTTPException: If the group is not found or user lacks permission
    """
    return schedule_crud.get_schedule_for_group(req_dep.db, group_api_id)
