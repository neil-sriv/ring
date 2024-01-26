from __future__ import annotations
from typing import TYPE_CHECKING
from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.schedule_model import Schedule
from ring.postgres_models.group_model import Group

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_schedule_for_group(db: Session, group_api_id: str) -> Schedule:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return group.schedule
