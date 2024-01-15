from __future__ import annotations
from typing import TYPE_CHECKING
from ring.postgres_models import Letter
from ring.pydantic_schemas.schemas import LetterCreate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models.group_model import Group


def get_letters(
    db: Session, group: Group, skip: int = 0, limit: int = 100
) -> list[Letter]:
    return (
        db.query(Letter).filter(Letter.group == group).offset(skip).limit(limit).all()
    )


def create_letter(db: Session, letter: LetterCreate) -> Letter:
    db_letter = Letter.create(letter.group)
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    return db_letter
