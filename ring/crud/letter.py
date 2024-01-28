from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select
from ring.postgres_models import Letter, Group
from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.question_model import Question

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_letters(
    db: Session, group_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Letter]:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def create_letter(db: Session, group_api_id: str) -> Letter:
    group = api_identifier_crud.get_model(
        db,
        Group,
        api_id=group_api_id,
    )
    db_letter = Letter.create(group)
    db.add(db_letter)
    return db_letter


def add_question(db: Session, letter: Letter, question_text: str) -> Question:
    question = Question.create(letter, question_text)
    db.add(question)
    letter.questions.append(question)
    return question
