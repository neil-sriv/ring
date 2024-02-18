from __future__ import annotations
from fastapi import Depends
from ring.dependencies import RequestDependencies, get_request_dependencies
from typing import Sequence
from ring.crud import (
    group as group_crud,
    api_identifier as api_identifier_crud,
)
from ring.pydantic_schemas import GroupLinked as GroupSchema
from ring.pydantic_schemas.group import GroupCreate
from ring.pydantic_schemas.schedule import ScheduleSendParam
from ring.routes import internal
from ring.postgres_models.group_model import Group


@internal.post("/group", response_model=GroupSchema)
async def create_group(
    group: GroupCreate,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Group:
    db_group = group_crud.create_group(
        db=req_dep.db, admin_api_id=group.admin_api_identifier, name=group.name
    )
    req_dep.db.commit()
    return db_group


@internal.get("/groups/", response_model=Sequence[GroupSchema])
async def list_groups(
    user_api_id: str,
    skip: int = 0,
    limit: int = 100,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Sequence[Group]:
    groups = group_crud.get_groups(
        req_dep.db,
        user_api_id=user_api_id,
        skip=skip,
        limit=limit,
    )
    return groups


@internal.get("/group/{group_api_id}", response_model=GroupSchema)
async def read_group(
    group_api_id: str,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db,
        Group,
        api_id=group_api_id,
    )
    return db_group


@internal.post(
    "/group/{group_api_id}:add_member/{user_api_id}",
    response_model=GroupSchema,
)
async def add_user_to_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Group:
    group = group_crud.add_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@internal.post(
    "/group/{group_api_id}:remove_member/{user_api_id}",
    response_model=GroupSchema,
)
async def remove_user_from_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Group:
    group = group_crud.remove_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@internal.post(
    "/group/{group_api_id}:schedule_send",
    response_model=GroupSchema,
)
async def schedule_send(
    group_api_id: str,
    schedule_param: ScheduleSendParam,
    req_dep: RequestDependencies = Depends(get_request_dependencies),
) -> Group:
    group = group_crud.schedule_send(
        req_dep.db,
        group_api_id=group_api_id,
        letter_api_id=schedule_param.letter_api_id,
        send_at=schedule_param.send_at,
    )
    req_dep.db.commit()
    return group
