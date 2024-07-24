from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select
from ring.postgres_models import Letter
from ring.api_identifier import util as api_identifier_crud
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_questions(
    db: Session, letter_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Question]:
    letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    return db.scalars(
        select(Question)
        .filter(Question.letter == letter)
        .offset(skip)
        .limit(
            limit,
        )
    ).all()


def _validate_response(
    question: Question,
    user: User,
) -> None:
    if user not in question.letter.participants:
        raise ValueError("User is not a participant in the letter.")
    if user.id in [resp.participant_id for resp in question.responses]:
        raise ValueError("User has already responded to this question.")


def add_response(
    db: Session,
    question: Question,
    user: User,
    response_text: str,
) -> Response:
    _validate_response(question, user)
    response = Response.create(user, question, response_text)
    db.add(response)
    question.responses.append(response)
    return response


def edit_response(
    db: Session,
    response: Response,
    response_text: str,
) -> Response:
    response.response_text = response_text
    db.add(response)
    return response
