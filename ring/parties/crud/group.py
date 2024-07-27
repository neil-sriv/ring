from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Sequence
from ring.api_identifier import util as api_identifier_crud
from ring.tasks.crud import (
    schedule as schedule_crud,
)
from ring.letters.models.letter_model import Letter
from ring.tasks.models.task_model import TaskType
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
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


def create_group(db: Session, admin_api_id: str, name: str) -> Group:
    admin_user = api_identifier_crud.get_model(
        db,
        User,
        api_id=admin_api_id,
    )
    db_letter = Group.create(name, admin_user)
    db.add(db_letter)
    return db_letter


def add_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    db_group.members.append(db_user)
    return db_group


def remove_member(db: Session, group_api_id: str, user_api_id: str) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_user = api_identifier_crud.get_model(db, User, api_id=user_api_id)
    db_group.members.remove(db_user)
    return db_group


def get_letter_by_api_id(group: Group, api_id: str) -> Letter:
    letter = next(
        filter(
            lambda letter: letter.api_identifier == api_id,
            group.letters,
        )
    )
    if not letter:
        raise ValueError(f"Could not find letter with api_id {api_id}")
    return letter


def schedule_send(
    db: Session, group_api_id: str, letter_api_id: str, send_at: datetime
) -> Group:
    db_group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    db_letter = get_letter_by_api_id(db_group, letter_api_id)
    schedule_crud.register_task(
        db,
        db_group.schedule,
        TaskType.SEND_EMAIL,
        send_at,
        {"letter_api_id": db_letter.api_identifier},
    )
    return db_group

def add_members(
    db: Session, group: Group, members: Sequence[User]
) -> None:
    for member in members:
        if member not in group.members:
            group.members.append(member)
