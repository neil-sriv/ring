from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from ring.crud import api_identifier as api_identifier_crud
from ring.pydantic_schemas import GroupCreate
from ring.postgres_models.group_model import Group
from ring.postgres_models.user_model import User
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_groups(
    db: Session, user_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Group]:
    user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    if not user:
        raise Exception("User not found")
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
        api_id=group.admin.api_identifier,
    )
    if not admin_user:
        raise Exception("Admin user not found")
    db_letter = Group.create(group.name, admin_user)
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter
