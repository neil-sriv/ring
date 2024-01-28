from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING, Sequence
from ring.crud import (
    group as group_crud,
    api_identifier as api_identifier_crud,
)
from ring.pydantic_schemas import GroupLinked as GroupSchema
from ring.pydantic_schemas.group import GroupCreate
from ring.pydantic_schemas.schedule import ScheduleSendParam
from ring.routes import internal
from ring.postgres_models.group_model import Group

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@internal.post("/group", response_model=GroupSchema)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
) -> Group:
    return group_crud.create_group(db=db, group=group)


@internal.get("/groups/", response_model=Sequence[GroupSchema])
def list_groups(
    user_api_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(
        get_db,
    ),
) -> Sequence[Group]:
    groups = group_crud.get_groups(
        db,
        user_api_id=user_api_id,
        skip=skip,
        limit=limit,
    )
    return groups


@internal.get("/group/{group_api_id}", response_model=GroupSchema)
def read_group(
    group_api_id: str,
    db: Session = Depends(get_db),
) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db_group


@internal.post(
    "/group/{group_api_id}:add_member/{user_api_id}",
    response_model=GroupSchema,
)
def add_user_to_group(
    group_api_id: str,
    user_api_id: str,
    db: Session = Depends(get_db),
) -> Group:
    group = group_crud.add_member(
        db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    return group


@internal.post(
    "/group/{group_api_id}:remove_member/{user_api_id}",
    response_model=GroupSchema,
)
def remove_user_from_group(
    group_api_id: str,
    user_api_id: str,
    db: Session = Depends(get_db),
) -> Group:
    group = group_crud.remove_member(
        db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    return group


@internal.post(
    "/group/{group_api_id}:schedule_send",
    response_model=GroupSchema,
)
def schedule_send(
    group_api_id: str,
    schedule_param: ScheduleSendParam,
    db: Session = Depends(get_db),
) -> Group:
    group = group_crud.schedule_send(
        db,
        group_api_id=group_api_id,
        letter_api_id=schedule_param.letter_api_id,
        send_at=schedule_param.send_at,
    )
    return group
