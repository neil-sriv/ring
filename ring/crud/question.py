from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select
from ring.postgres_models import Letter
from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.question_model import Question
from ring.postgres_models.response_model import Response
from ring.postgres_models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_questions(
    db: Session, letter_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Question]:
    letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    return db.scalars(
        select(Question).filter(Question.letter == letter).offset(skip).limit(limit)
    ).all()


def add_response(
    db: Session,
    question: Question,
    user: User,
    response_text: str,
) -> Response:
    response = Response.create(user, question, response_text)
    db.add(response)
    question.responses.append(response)
    return response
