from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select
from ring.postgres_models import Letter, Group
from ring.crud import api_identifier as api_identifier_crud

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.pydantic_schemas import LetterCreate


def get_letters(
    db: Session, group_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Letter]:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def create_letter(db: Session, letter: LetterCreate) -> Letter:
    group = api_identifier_crud.get_model(
        db,
        Group,
        api_id=letter.group_api_identifier,
    )
    db_letter = Letter.create(group)
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter
