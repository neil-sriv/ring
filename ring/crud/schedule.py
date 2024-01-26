from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.schedule_model import Schedule
from ring.pydantic_schemas import GroupCreate
from ring.postgres_models.group_model import Group
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_schedule_for_group(db: Session, group_api_id: str) -> Schedule:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    if not group:
        raise Exception("User not found")
    return group.schedule