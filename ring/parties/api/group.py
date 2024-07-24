from __future__ import annotations
from fastapi import APIRouter, Depends
from datetime import timezone
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from typing import Sequence
from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.parties.crud import group as group_crud
from ring.ring_pydantic import GroupLinked as GroupSchema
from ring.parties.schemas.group import GroupCreate, GroupUpdate
from ring.tasks.schemas.schedule import ScheduleSendParam
from ring.parties.models.group_model import Group

router = APIRouter()


@router.post("/group", response_model=GroupSchema)
async def create_group(
    group: GroupCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = group_crud.create_group(
        db=req_dep.db, admin_api_id=group.admin_api_identifier, name=group.name
    )
    req_dep.db.commit()
    return db_group


@router.get("/groups/", response_model=Sequence[GroupSchema])
async def list_groups(
    user_api_id: str,
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[Group]:
    groups = group_crud.get_groups(
        req_dep.db,
        user_api_id=user_api_id,
        skip=skip,
        limit=limit,
    )
    return groups


@router.get("/group/{group_api_id}", response_model=GroupSchema)
async def read_group(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db,
        Group,
        api_id=group_api_id,
    )
    return db_group


@router.post(
    "/group/{group_api_id}:add_member/{user_api_id}",
    response_model=GroupSchema,
)
async def add_user_to_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    group = group_crud.add_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@router.post(
    "/group/{group_api_id}:remove_member/{user_api_id}",
    response_model=GroupSchema,
)
async def remove_user_from_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    group = group_crud.remove_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@router.post(
    "/group/{group_api_id}:schedule_send",
    response_model=GroupSchema,
)
async def schedule_send(
    group_api_id: str,
    schedule_param: ScheduleSendParam,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    utc_send_at = schedule_param.send_at.astimezone(tz=timezone.utc)
    group = group_crud.schedule_send(
        req_dep.db,
        group_api_id=group_api_id,
        letter_api_id=schedule_param.letter_api_id,
        send_at=utc_send_at,
    )
    req_dep.db.commit()
    return group


@router.patch(
    "/group/{group_api_id}",
    deprecated=True,
)
def update_group(
    group_api_id: str,
    group: GroupUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> None:
    raise NotImplementedError()
