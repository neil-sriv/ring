from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING, Sequence
from ring.crud import group as group_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas import GroupLinked as GroupSchema, GroupCreate
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models.group_model import Group


@internal.post("/group", response_model=GroupSchema)
def create_group(group: GroupCreate, db: Session = Depends(get_db)) -> Group:
    return group_crud.create_group(db=db, group=group)


@internal.get("/groups/", response_model=Sequence[GroupSchema])
def list_groups(
    user_api_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Sequence[Group]:
    groups = group_crud.get_groups(db, user_api_id=user_api_id, skip=skip, limit=limit)
    return groups


@internal.get("/group/{group_api_id}", response_model=GroupSchema)
def read_group(group_api_id: str, db: Session = Depends(get_db)) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db_group
