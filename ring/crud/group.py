from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Sequence
from ring.crud import api_identifier as api_identifier_crud
from ring.pydantic_schemas.group import GroupCreate
from ring.postgres_models.group_model import Group
from ring.postgres_models.user_model import User
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_groups(
    db: Session, user_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Group]:
    user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    return db.scalars(
        select(Group)
        .filter(
            Group.members.contains(user),
        )
        .offset(skip)
        .limit(limit)
    ).all()


def create_group(db: Session, group: GroupCreate) -> Group:
    admin_user = api_identifier_crud.get_model(
        db,
        User,
        api_id=group.admin_api_identifier,
    )
    db_letter = Group.create(group.name, admin_user)
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter


def add_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    db_group.members.append(db_user)
    db.commit()
    db.refresh(db_group)
    return db_group


def remove_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    db_group.members.remove(db_user)
    db.commit()
    db.refresh(db_group)
    return db_group


def schedule_send(
    db: Session, group_api_id: str, letter_api_id: str, send_at: datetime
) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_letter = db_group.get_letter_by_api_id(letter_api_id)
    db_group.schedule_send_email(db_letter, send_at)
    db.commit()
    db.refresh(db_group)
    return db_group
