from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from ring.postgres_models import Letter
from ring.pydantic_schemas.schemas import LetterCreate
from ring.postgres_models.group_model import Group
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models.user_model import User


def get_groups(
    db: Session, user: User, skip: int = 0, limit: int = 100
) -> Sequence[Group]:
    return db.scalars(
        select(Group).filter(Group.admin == user).offset(skip).limit(limit)
    ).all()


def create_letter(db: Session, letter: LetterCreate) -> Letter:
    db_letter = Letter.create(letter.group)
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter
